import json
import mimetypes
import subprocess
import logging
import os
import yaml
import time
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

    # 对于视频文件，使用 FileResponse 并支持 Range 请求
    if content_type and content_type.startswith('video/'):
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Accept-Ranges'] = 'bytes'
        return response

    return FileResponse(open(file_path, 'rb'), content_type=content_type or 'application/octet-stream')

logger = logging.getLogger(__name__)

# 视频存储根目录 (server/media/videos)
SERVER_ROOT = Path(__file__).resolve().parent.parent.parent.parent
VIDEOS_ROOT = SERVER_ROOT / 'media' / 'videos'
VIDEOS_ROOT.mkdir(parents=True, exist_ok=True)


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
    """检查视频是否已缓存且有效（有时长 > 0，且非 H.265 编码）"""
    cache_path = _get_video_cache_path(start_time, end_time, camera_index, record_id)
    if not cache_path.exists() or cache_path.stat().st_size < 10000:
        return None
    # 验证 MP4 文件有时长，避免返回之前生成的 0 时长文件
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-show_entries", "stream=codec_name", "-select_streams", "v:0",
             "-of", "json", str(cache_path)],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            data = json.loads(r.stdout)
            dur = float(data.get("format", {}).get("duration") or 0)
            # 检查编码格式，H.265 需要重新转码
            streams = data.get("streams", [])
            codec = streams[0].get("codec_name", "").lower() if streams else ""
            if codec in ("hevc", "h265"):
                print(f"[Cache] 缓存文件为 H.265 编码，需重新转码: {cache_path}")
                cache_path.unlink(missing_ok=True)
                return None
            if dur > 0:
                print(f"[Cache] 视频已缓存且有效: {cache_path}, 时长 {dur:.1f}s")
                return cache_path
            else:
                print(f"[Cache] 缓存文件时长为0，删除: {cache_path}")
                cache_path.unlink(missing_ok=True)
                return None
    except Exception as e:
        logger.warning(f"Cache verify failed: {e}")
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
    """生成RTSP回放URL（返回多个用于重试）"""
    start_compact = _to_compact(start_time)
    end_compact = _to_compact(end_time)

    sep = '/' if not rtsp_base.endswith('/') else ''
    url = f"{rtsp_base}{sep}?starttime={start_compact}&endtime={end_compact}"

    print("="*80)
    print(f"📌 RTSP回放地址: {url}")
    print("="*80)

    # 返回 3 个相同 URL，用于重试（NVR 第一次连接可能不稳定）
    return [url, url, url]


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


        rtsp_urls = _build_rtsp_urls(rtsp_base, start_time, end_time)

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
        # 用相对路径，避免返回后端内部地址（127.0.0.1:8000）
        mp4_url = f"/media/videos/{filename}?v={ts}"
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