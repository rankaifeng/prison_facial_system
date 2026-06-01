import json
import subprocess
import logging
import os
import yaml
import uuid
import time
import shutil
from io import BytesIO
from pathlib import Path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.users.config import JWTAuthentication

logger = logging.getLogger(__name__)

HLS_ROOT = Path('/tmp/hls_streams')
HLS_ROOT.mkdir(parents=True, exist_ok=True)


def load_cameras_config():
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        'config', 'cameras.yml'
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load camera config: {e}")
        return {'cameras': []}


def _build_rtsp_urls(rtsp_base, start_time, end_time):
    """生成多种RTSP URL格式，按优先级排列"""
    start = start_time if start_time.endswith('Z') else f"{start_time}Z"
    end = end_time if end_time.endswith('Z') else f"{end_time}Z"

    def to_iso(t):
        t_clean = t.replace('Z', '')
        if 'T' in t_clean and len(t_clean.split('T')[0]) == 8 and '-' not in t_clean:
            d, tm = t_clean.split('T')
            d = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            tm = f"{tm[:2]}:{tm[2:4]}:{tm[4:]}"
            return f"{d}T{tm}Z"
        return t

    start_iso = to_iso(start_time)
    end_iso = to_iso(end_time)
    sep = '/' if not rtsp_base.endswith('/') else ''

    return [
        f"{rtsp_base}{sep}?starttime={start}&endtime={end}",
        f"{rtsp_base}?starttime={start}&endtime={end}",
        f"{rtsp_base}{sep}?starttime={start_iso}&endtime={end_iso}",
        f"{rtsp_base}?starttime={start_iso}&endtime={end_iso}",
        rtsp_base.rstrip('/'),
    ]


def _try_ffmpeg_hls(rtsp_url, session_dir, max_wait=10):
    """尝试用FFmpeg将RTSP转为HLS"""
    playlist_path = session_dir / 'playlist.m3u8'
    seg_pattern = str(session_dir / 'seg_%03d.ts')

    ffmpeg_cmd = [
        'ffmpeg',
        '-loglevel', 'error',
        '-rtsp_transport', 'tcp',
        '-timeout', '10000000',
        '-i', rtsp_url,
        '-c', 'copy',
        '-f', 'hls',
        '-hls_time', '1',
        '-hls_list_size', '0',
        '-hls_segment_filename', seg_pattern,
        '-hls_flags', 'independent_segments',
        '-y',
        str(playlist_path),
    ]

    logger.info(f"FFmpeg HLS: {rtsp_url}")
    process = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    # Save PID for targeted cleanup
    try:
        with open(session_dir / '.pid', 'w') as f:
            f.write(str(process.pid))
    except Exception:
        pass

    def _reap():
        try:
            process.wait(timeout=3)
        except Exception:
            pass

    start_wait = time.time()
    while time.time() - start_wait < max_wait:
        if playlist_path.exists():
            segs = sorted(session_dir.glob('seg_*.ts'))
            if segs:
                # Verify m3u8 actually has segment entries (not just header)
                try:
                    content = playlist_path.read_text()
                    if 'EXTINF' in content and 'seg_' in content:
                        logger.info(f"HLS ready: {playlist_path.name}, {len(segs)} segs, {len(content)}b")
                        # Keep FFmpeg running in background, PID saved for later cleanup
                        return True, None
                except Exception:
                    pass  # File not fully written yet, keep waiting

        if process.poll() is not None:
            stderr = process.stderr.read().decode('utf-8', errors='replace')
            error_lines = [l.strip() for l in stderr.split('\n') if l.strip()]
            real_errors = [l for l in error_lines if not l.startswith('ffmpeg version')]
            last_error = real_errors[-1] if real_errors else '未知错误'
            _reap()
            logger.error(f"FFmpeg exit(code={process.returncode}): {stderr[:500]}")
            return False, last_error

        time.sleep(0.3)

    process.kill()
    _reap()
    return False, '连接摄像头超时'


def recover_hls_stream(session_id):
    """从session元数据恢复HLS流"""
    session_dir = HLS_ROOT / session_id
    meta_path = session_dir / '.session.json'
    if not meta_path.exists():
        logger.info(f"No metadata for session {session_id}, cannot recover")
        return False

    try:
        with open(meta_path) as f:
            meta = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read session metadata: {e}")
        return False

    session_dir.mkdir(parents=True, exist_ok=True)
    success, error = _try_ffmpeg_hls(meta['rtsp_url'], session_dir, max_wait=10)
    if success:
        logger.info(f"Recovered HLS stream for session {session_id}")
    else:
        logger.error(f"Failed to recover HLS stream: {error}")
    return success


class VideoStreamUrlController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            return self._handle(request)
        except Exception as e:
            logger.error(f"VideoStreamUrlController error: {e}", exc_info=True)
            return Response({
                'code': 0, 'msg': f'服务器内部错误: {str(e)[:100]}', 'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _handle(self, request):
        start_time = request.query_params.get('start_time', '').strip()
        end_time = request.query_params.get('end_time', '').strip()
        camera_index = int(request.query_params.get('camera', 0))

        if not start_time or not end_time:
            return Response({
                'code': 0, 'msg': '缺少开始时间或结束时间', 'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        config = load_cameras_config()
        cameras = config.get('cameras', [])

        if camera_index >= len(cameras):
            return Response({
                'code': 0, 'msg': '摄像头不存在', 'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        camera = cameras[camera_index]
        if not camera.get('enabled'):
            return Response({
                'code': 0, 'msg': '摄像头未启用', 'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        rtsp_base = camera.get('rtsp_url', '')
        if not rtsp_base:
            return Response({
                'code': 0, 'msg': '摄像头RTSP地址未配置', 'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        cleanup_old_streams()

        rtsp_urls = _build_rtsp_urls(rtsp_base, start_time, end_time)

        last_error = None
        for i, rtsp_url in enumerate(rtsp_urls):
            session_id = uuid.uuid4().hex[:12]
            session_dir = HLS_ROOT / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            max_wait = 120 if i == len(rtsp_urls) - 1 else 90
            success, error = _try_ffmpeg_hls(rtsp_url, session_dir, max_wait=max_wait)
            if success:
                # Save session metadata for recovery
                is_live = (i == len(rtsp_urls) - 1)
                try:
                    with open(session_dir / '.session.json', 'w') as f:
                        json.dump({
                            'rtsp_url': rtsp_url,
                            'camera_index': camera_index,
                            'start_time': start_time,
                            'end_time': end_time,
                            'is_live': is_live,
                            'created_at': time.time(),
                        }, f)
                except Exception as e:
                    logger.warning(f"Failed to save session metadata: {e}")
                return self._build_response(request, session_id, camera, is_live)

            if error:
                last_error = error
            shutil.rmtree(session_dir, ignore_errors=True)

        user_msg = self._translate_error(last_error or '未知错误')
        return Response({
            'code': 0, 'msg': f'视频流转换失败: {user_msg}', 'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _translate_error(self, msg):
        m = msg.lower()
        if '400' in m:
            return '摄像头不支持以URL参数回放，请检查摄像头是否支持RTSP回放功能'
        if 'connection refused' in m or 'connection timed out' in m:
            return '无法连接摄像头，请检查网络和摄像头状态'
        if 'authentication' in m or '401' in m:
            return '摄像头认证失败，请检查用户名密码'
        if 'not found' in m:
            return '未找到指定的视频流'
        if 'timeout' in m:
            return '连接摄像头超时'
        if 'invalid' in m:
            return '无效的RTSP视频流'
        return msg.strip()[:80]

    def _build_response(self, request, session_id, camera, is_live=False):
        import time
        ts = int(time.time())
        m3u8_url = f"{request.scheme}://{request.get_host()}/media/hls/{session_id}/playlist.m3u8?v={ts}"
        return Response({
            'code': 1,
            'msg': 'success' if not is_live else '未找到录像，当前为实时画面',
            'data': {
                'url': m3u8_url,
                'session_id': session_id,
                'camera_name': camera.get('name'),
                'channel': camera.get('channel'),
                'is_live': is_live,
            }
        })


def _kill_ffmpeg(session_dir):
    """按PID杀死与session关联的FFmpeg进程并回收"""
    pid_file = session_dir / '.pid'
    if not pid_file.exists():
        return
    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())
        os.kill(pid, 15)  # SIGTERM
        # Wait and reap
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass  # Already reaped
    except (ProcessLookupError, ValueError, OSError):
        pass


def cleanup_old_streams():
    now = time.time()
    for d in HLS_ROOT.iterdir():
        if not d.is_dir():
            continue
        mtime = d.stat().st_mtime
        if now - mtime > 300:
            _kill_ffmpeg(d)
            shutil.rmtree(d, ignore_errors=True)
            logger.info(f"Cleaned up stale HLS dir: {d.name}")


class CameraListController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        config = load_cameras_config()
        cameras = config.get('cameras', [])

        camera_list = [
            {
                'index': idx,
                'name': cam.get('name'),
                'channel': cam.get('channel'),
                'enabled': cam.get('enabled', False),
            }
            for idx, cam in enumerate(cameras)
        ]

        return Response({
            'code': 1,
            'msg': 'success',
            'data': camera_list
        })


from django.http import FileResponse, HttpResponseNotFound


def _generate_m3u8(session_dir):
    """从现有分片动态生成m3u8内容"""
    segs = sorted(session_dir.glob('seg_*.ts'))
    if not segs:
        return None
    lines = [
        '#EXTM3U',
        '#EXT-X-VERSION:6',
        '#EXT-X-TARGETDURATION:2',
        '#EXT-X-MEDIA-SEQUENCE:0',
        '#EXT-X-INDEPENDENT-SEGMENTS',
    ]
    for seg in segs:
        duration = 2.0  # default
        lines.append(f'#EXTINF:{duration:.3f},')
        lines.append(seg.name)
    return '\n'.join(lines) + '\n'


def serve_hls(request, path):
    """提供HLS流媒体文件(m3u8/ts)，文件不存在时自动恢复"""
    # 去掉query string
    path = path.split('?')[0]
    file_path = os.path.join(str(HLS_ROOT), path)
    real_path = os.path.realpath(file_path)
    if not real_path.startswith(os.path.realpath(str(HLS_ROOT))):
        return HttpResponseNotFound('Invalid path')

    session_id = path.split('/')[0] if '/' in path else ''
    session_dir = HLS_ROOT / session_id if session_id else None

    def _m3u8_response(content, from_file=False):
        content_type = 'application/vnd.apple.mpegurl'
        if from_file:
            resp = FileResponse(open(content, 'rb'), content_type=content_type)
        else:
            resp = FileResponse(BytesIO(content.encode()), content_type=content_type)
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Cache-Control'] = 'no-cache'
        return resp

    def _ts_response(filepath):
        resp = FileResponse(open(filepath, 'rb'), content_type='video/MP2T')
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Cache-Control'] = 'no-cache'
        return resp

    # m3u8: 直接从分片生成m3u8内容
    if path.endswith('/playlist.m3u8'):
        # 先生成m3u8内容，确保有足够的分片
        max_wait = 3.0  # 最多等3秒
        start = time.time()
        generated = None

        while time.time() - start < max_wait:
            if session_dir and session_dir.exists():
                generated = _generate_m3u8(session_dir)
                if generated:
                    seg_count = generated.count('#EXTINF')
                    if seg_count >= 5:
                        break
            time.sleep(0.2)
            generated = None

        if generated:
            logger.info(f"Serving m3u8 with {generated.count('#EXTINF')} segments for {session_id}")
            return _m3u8_response(generated)

    # .ts分片: 直接返回文件
    if not os.path.exists(real_path):
        return HttpResponseNotFound('File not found')

    return _ts_response(real_path)
