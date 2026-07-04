import json
import mimetypes
import subprocess
import logging
import os
import yaml
import uuid
import time
import shutil
from io import BytesIO
from pathlib import Path
from django.http import FileResponse, Http404
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.users.config import JWTAuthentication


def serve_media(request, path):
    """自定义 media 文件服务（不依赖 Django static()，兼容 Daphne/Channels）"""
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise Http404
    content_type, _ = mimetypes.guess_type(file_path)
    return FileResponse(open(file_path, 'rb'), content_type=content_type or 'application/octet-stream')

logger = logging.getLogger(__name__)

# 视频存储根目录 (server/media/videos)
SERVER_ROOT = Path(__file__).resolve().parent.parent.parent.parent
VIDEOS_ROOT = SERVER_ROOT / 'media' / 'videos'
VIDEOS_ROOT.mkdir(parents=True, exist_ok=True)

# 兼容旧代码 (HLS相关功能)
HLS_ROOT = VIDEOS_ROOT


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


def _parse_iso_time(t):
    """解析ISO 8601时间字符串，返回UTC时间戳"""
    t = t.replace('Z', '')
    # 2026-06-01T15:19:44 或 20260601T151944
    if len(t) == 15 and 'T' in t:  # 紧凑格式 20260601T151944
        date, time_str = t.split('T')
        t = f"{date[:4]}-{date[4:6]}-{date[6:]}T{time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
    from datetime import datetime
    return datetime.fromisoformat(t.replace('T', ' '))


def _calc_duration_seconds(start_time, end_time):
    """计算两个时间字符串之间的秒数"""
    try:
        start = _parse_iso_time(start_time)
        end = _parse_iso_time(end_time)
        delta = end - start
        seconds = int(delta.total_seconds())
        return max(seconds, 1)  # 至少1秒
    except Exception as e:
        logger.warning(f"Failed to parse time: {e}")
        return 60  # 默认60秒


def _get_video_cache_path(start_time, end_time, camera_index, record_id=None):
    """根据时间范围和摄像头索引生成缓存文件路径"""
    # 清理时间字符串，生成唯一文件名
    start_clean = start_time.replace(':', '').replace('-', '').replace('T', '_').replace('Z', '')
    end_clean = end_time.replace(':', '').replace('-', '').replace('T', '_').replace('Z', '')
    # 加入 record_id 确保每个记录有唯一文件，避免并发冲突
    if record_id:
        return VIDEOS_ROOT / f"cam{camera_index}_{start_clean}_{end_clean}_r{record_id}.mp4"
    return VIDEOS_ROOT / f"cam{camera_index}_{start_clean}_{end_clean}.mp4"


def _video_exists_cached(start_time, end_time, camera_index, record_id=None):
    """检查视频是否已缓存"""
    cache_path = _get_video_cache_path(start_time, end_time, camera_index, record_id)
    if cache_path.exists() and cache_path.stat().st_size > 10000:
        print(f"[Cache] 视频已缓存: {cache_path}")
        return cache_path
    return None


def _to_compact(t):
    """将时间转换为紧凑格式 YYYYMMDDThhmmssZ"""
    t_clean = t.replace('Z', '')
    # 如果已经是紧凑格式（日期8位+T+时间6位）
    if len(t_clean) == 15 and 'T' in t_clean:
        return t_clean + 'Z'
    # 如果是 ISO 格式（YYYY-MM-DDThh:mm:ss）
    if 'T' in t_clean and '-' in t_clean:
        date_part, time_part = t_clean.split('T')
        date_part = date_part.replace('-', '')
        time_part = time_part.replace(':', '')
        return date_part + 'T' + time_part[:6] + 'Z'
    # 已经是其他格式，直接加 Z
    return t_clean + 'Z'


def _build_rtsp_urls(rtsp_base, start_time, end_time):
    """生成RTSP回放URL"""
    start_compact = _to_compact(start_time)
    end_compact = _to_compact(end_time)

    sep = '/' if not rtsp_base.endswith('/') else ''
    url = f"{rtsp_base}{sep}?starttime={start_compact}&endtime={end_compact}"

    print("="*80)
    print(f"📌 RTSP回放地址: {url}")
    print("="*80)

    return [url]


def _try_ffmpeg_mp4(rtsp_url, output_path, duration, max_wait=120):
    """尝试用FFmpeg将RTSP下载为MP4"""
    # 流拷贝模式：保留原编码，快速下载
    ffmpeg_cmd = [
        'ffmpeg',
        '-loglevel', 'warning',
        '-rtsp_transport', 'tcp',
        '-i', rtsp_url,
        '-an',
        '-c', 'copy',
        '-movflags', '+faststart',
        '-t', str(duration),
        '-y',
        str(output_path),
    ]

    mp4_path = output_path

    logger.info(f"FFmpeg MP4: {rtsp_url}")
    print(f"[FFmpeg] 开始转换")
    print(f"[FFmpeg] 目标时长: {duration} 秒")
    print(f"[FFmpeg] 输出路径: {output_path}")
    print(f"[FFmpeg] 等待文件生成, 最大等待: {max_wait}秒")
    process = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    def _reap():
        try:
            process.wait(timeout=3)
        except Exception:
            pass

    start_wait = time.time()
    while time.time() - start_wait < max_wait:
        if process.poll() is not None:
            if process.returncode != 0:
                stderr = process.stderr.read().decode('utf-8', errors='replace')
                logger.error(f"FFmpeg exit(code={process.returncode}): {stderr[:500]}")
                print(f"[FFmpeg] ffmpeg进程异常退出, code={process.returncode}, stderr={stderr[:500]}")
                return False, '下载录像失败'
            break

        # 检查文件是否已经有一定大小
        if mp4_path.exists():
            size = mp4_path.stat().st_size
            print(f"[FFmpeg] 文件已生成, 大小: {size} bytes")
            if size > 10000:
                print(f"[FFmpeg] 文件大小满足要求({size} > 10000), 等待ffmpeg结束...")

        time.sleep(0.5)

    if process.poll() is not None:
        _reap()
    else:
        process.kill()
        _reap()
        print(f"[FFmpeg] 等待超时, kill掉ffmpeg进程")
        return False, '下载录像超时'

    if not mp4_path.exists() or mp4_path.stat().st_size < 10000:
        print(f"[FFmpeg] 文件无效或大小不足")
        return False, '下载录像文件无效'

    print(f"[FFmpeg] MP4生成成功: {mp4_path.name}, size={mp4_path.stat().st_size}")
    logger.info(f"MP4 ready: {mp4_path.name}, size={mp4_path.stat().st_size}")
    return True, None


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

    logger.info(f"HLS recovery is disabled for session {session_id}; MP4 playback is used instead")
    return False


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
        logger.info("Recovered HLS stream for session {rtsp_urls}")

        # 计算录像时长（秒）
        duration = _calc_duration_seconds(start_time, end_time)
        print(f"[FFmpeg] 录像时长: {duration} 秒")

        # 先检查是否已有缓存
        cached_path = _video_exists_cached(start_time, end_time, camera_index)
        if cached_path:
            print(f"[Cache] 命中缓存，直接返回: {cached_path}")
            return self._build_response(request, cached_path.name, camera, False, is_cached=True)

        from apps.users.rtsp_to_mp4 import record_rtsp_to_mp4

        last_error = None
        for i, rtsp_url in enumerate(rtsp_urls):
            video_path = _get_video_cache_path(start_time, end_time, camera_index)
            video_path.parent.mkdir(parents=True, exist_ok=True)

            max_wait = duration + 30
            result = record_rtsp_to_mp4(
                rtsp_url=rtsp_url,
                output_path=str(video_path),
                duration=duration,
                timeout=max_wait,
                stall_timeout=30,
                overwrite=True,
                pre_probe=True,
                verbose=True,
            )
            if result["success"]:
                print(f"[FFmpeg] 视频下载完成: {video_path}")
                return self._build_response(request, video_path.name, camera, False, is_cached=False)

            if result["message"]:
                last_error = result["message"]
                print(f"[FFmpeg] URL {i+1} 失败: {last_error}")

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

    def _build_response(self, request, filename, camera, is_live=False, is_cached=False):
        import time
        ts = int(time.time())
        # 视频文件直接通过 media/videos/ 路径访问
        mp4_url = f"{request.scheme}://{request.get_host()}/media/videos/{filename}?v={ts}"
        return Response({
            'code': 1,
            'msg': '缓存命中' if is_cached else ('success' if not is_live else '未找到录像，当前为实时画面'),
            'data': {
                'url': mp4_url,
                'filename': filename,
                'camera_name': camera.get('name'),
                'channel': camera.get('channel'),
                'is_live': is_live,
                'is_cached': is_cached,
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

    # .mp4: 直接返回文件
    if path.endswith('.mp4'):
        if not os.path.exists(real_path):
            return HttpResponseNotFound('File not found')
        resp = FileResponse(open(real_path, 'rb'), content_type='video/mp4')
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Cache-Control'] = 'no-cache'
        return resp

    # .ts分片: 直接返回文件
    if not os.path.exists(real_path):
        return HttpResponseNotFound('File not found')

    return _ts_response(real_path)