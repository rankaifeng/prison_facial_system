import json
import subprocess
import logging
import os
import re
import socket
import hashlib
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


def _to_iso_format(t):
    """将时间转换为ISO格式 YYYY-MM-DDThh:mm:ssZ"""
    t_clean = t.replace('Z', '')
    # 紧凑格式 20260601T151944
    if len(t_clean) == 15 and 'T' in t_clean:
        date_part, time_part = t_clean.split('T')
        return f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]}T{time_part[:2]}:{time_part[2:4]}:{time_part[4:]}Z"
    # 已经是ISO格式
    if 'T' in t_clean and '-' in t_clean:
        return t_clean + 'Z'
    return t_clean + 'Z'


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


def _to_clock_format(t):
    """将时间转换为海康威视Range头的紧凑格式 YYYYMMDDThhmmssZ"""
    t_clean = t.replace('Z', '')
    if len(t_clean) == 15 and 'T' in t_clean:
        return t_clean + 'Z'
    if 'T' in t_clean and '-' in t_clean:
        date_part, time_part = t_clean.split('T')
        date_part = date_part.replace('-', '')
        time_part = time_part.replace(':', '')
        return date_part + 'T' + time_part[:6] + 'Z'
    return t_clean + 'Z'


def _parse_rtsp_url(rtsp_url):
    """从RTSP URL中解析出 user, password, host, port, channel"""
    match = re.match(r'rtsp://([^:]+):([^@]+)@([^:]+):?(\d+)?(.*)', rtsp_url)
    if not match:
        return None
    user, password, host, port, path = match.groups()
    port = port or '554'
    channel_match = re.search(r'/tracks/(\d+)', path)
    channel = channel_match.group(1) if channel_match else None
    return {'user': user, 'password': password, 'host': host, 'port': port, 'channel': channel}


def _build_isapi_urls(rtsp_base, start_time, end_time):
    """构建海康威视ISAPI HTTP回放URL（ffmpeg能正确处理时间参数）"""
    info = _parse_rtsp_url(rtsp_base)
    if not info or not info['channel']:
        return []

    start_iso = _to_iso_format(start_time)
    end_iso = _to_iso_format(end_time)

    user = info['user']
    pwd = info['password']
    host = info['host']
    channel = info['channel']

    # 海康威视ISAPI HTTP回放接口
    return [
        f"http://{user}:{pwd}@{host}/ISAPI/ContentMgmt/tracks/{channel}?starttime={start_iso}&endtime={end_iso}",
        f"http://{user}:{pwd}@{host}:80/ISAPI/ContentMgmt/tracks/{channel}?starttime={start_iso}&endtime={end_iso}",
    ]


def _build_rtsp_urls(rtsp_base, start_time, end_time):
    """生成多种回放URL格式，按优先级排列：ISAPI HTTP优先，RTSP作为备选"""
    urls = []

    # 优先使用海康威视ISAPI HTTP接口（ffmpeg能正确处理时间参数）
    isapi_urls = _build_isapi_urls(rtsp_base, start_time, end_time)
    urls.extend(isapi_urls)

    # RTSP回放作为备选
    start_compact = _to_compact(start_time)
    end_compact = _to_compact(end_time)
    start_iso = _to_iso_format(start_time)
    end_iso = _to_iso_format(end_time)

    sep = '/' if not rtsp_base.endswith('/') else ''

    urls.extend([
        f"{rtsp_base}{sep}?starttime={start_compact}&endtime={end_compact}",
        f"{rtsp_base}{sep}?starttime={start_iso}&endtime={end_iso}",
        rtsp_base.rstrip('/'),
    ])

    print("="*80)
    print("📌 最终生成的回放地址：")
    for url in urls:
        print(url)
    print("="*80)

    return urls


def _rtsp_digest_auth(method, uri, params, user, password):
    """计算RTSP Digest认证头（海康威视不使用qop）"""
    realm = params.get('realm', '')
    nonce = params.get('nonce', '')
    ha1 = hashlib.md5(f'{user}:{realm}:{password}'.encode()).hexdigest()
    ha2 = hashlib.md5(f'{method}:{uri}'.encode()).hexdigest()
    response = hashlib.md5(f'{ha1}:{nonce}:{ha2}'.encode()).hexdigest()
    return f'Digest username="{user}", realm="{realm}", nonce="{nonce}", uri="{uri}", response="{response}"'


def _parse_rtsp_digest_params(resp_text):
    """从401响应中提取Digest认证参数"""
    for line in resp_text.split('\r\n'):
        if line.lower().startswith('www-authenticate:'):
            www_auth = line.split(':', 1)[1].strip()
            params = {}
            for m in re.finditer(r'(\w+)="([^"]*)"', www_auth):
                params[m.group(1)] = m.group(2)
            for m in re.finditer(r'(\w+)=([^,\s"]+)', www_auth):
                if m.group(1) not in params:
                    params[m.group(1)] = m.group(2)
            return params
    return {}


def _rtsp_send(sock, method, uri, cseq, extra_headers=''):
    """发送RTSP请求并接收响应"""
    msg = f'{method} {uri} RTSP/1.0\r\nCSeq: {cseq}\r\n{extra_headers}\r\n'
    sock.send(msg.encode())
    resp = b''
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                break
            resp += data
            if b'\r\n\r\n' in resp:
                break
        except Exception:
            break
    return resp.decode('utf-8', errors='replace')


def _rtsp_auth_send(sock, method, uri, cseq, user, password, digest_params, extra_headers=''):
    """发送带Digest认证的RTSP请求"""
    auth = _rtsp_digest_auth(method, uri, digest_params, user, password)
    headers = f'Authorization: {auth}\r\n{extra_headers}'
    return _rtsp_send(sock, method, uri, cseq, headers)


def _download_rtsp_with_range(rtsp_url, start_time, end_time, output_path, duration, max_wait=120):
    """
    通过RTSP协议的Range头实现时间回放下载。
    解决海康威视NVR不响应URL中starttime/endtime参数的问题。
    方式：手动RTSP协商 + Range头指定时间段 → 提取RTP中的H.264数据 → ffmpeg封装为MP4。
    """
    info = _parse_rtsp_url(rtsp_url)
    if not info:
        return False, '无法解析RTSP地址'

    host = info['host']
    port = int(info['port'])
    user = info['user']
    password = info['password']

    start_clock = _to_clock_format(start_time)
    end_clock = _to_clock_format(end_time)

    sock = None

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15)
        sock.connect((host, port))

        cseq = 1

        # Step 1: OPTIONS 获取Digest challenge
        resp = _rtsp_send(sock, 'OPTIONS', rtsp_url, cseq)
        cseq += 1
        if '401' not in resp.split('\r\n')[0]:
            return False, 'RTSP OPTIONS未返回401'

        digest_params = _parse_rtsp_digest_params(resp)
        if not digest_params:
            return False, '无法解析Digest参数'

        # Step 2: OPTIONS + auth
        resp = _rtsp_auth_send(sock, 'OPTIONS', rtsp_url, cseq, user, password, digest_params)
        cseq += 1
        if '200' not in resp.split('\r\n')[0]:
            return False, f'OPTIONS认证失败'

        # Step 3: DESCRIBE + auth
        resp = _rtsp_auth_send(sock, 'DESCRIBE', rtsp_url, cseq, user, password,
                               digest_params, 'Accept: application/sdp\r\n')
        cseq += 1
        if '200' not in resp.split('\r\n')[0]:
            return False, f'DESCRIBE失败'

        # 解析SDP获取track control URL和编码信息
        sdp = resp.split('\r\n\r\n', 1)[1] if '\r\n\r\n' in resp else ''
        control_match = re.search(r'a=control:(trackID=\S+)', sdp)
        track_url = f'{rtsp_url}/{control_match.group(1)}' if control_match else rtsp_url

        # Step 4: SETUP (TCP interleaved, RTP/AVP)
        resp = _rtsp_auth_send(sock, 'SETUP', track_url, cseq, user, password,
                               digest_params, 'Transport: RTP/AVP/TCP;unicast;interleaved=0-1\r\n')
        cseq += 1
        if '200' not in resp.split('\r\n')[0]:
            return False, f'SETUP失败'

        session = ''
        for line in resp.split('\r\n'):
            if line.lower().startswith('session:'):
                session = line.split(':', 1)[1].strip().split(';')[0]

        # Step 5: PLAY with Range头 — 指定时间段回放（海康威视要求紧凑格式无Z）
        range_header = f'Range: clock={start_clock}-{end_clock}\r\n'
        session_header = f'Session: {session}\r\n' if session else ''
        resp = _rtsp_auth_send(sock, 'PLAY', rtsp_url, cseq, user, password,
                               digest_params, f'{session_header}{range_header}')
        cseq += 1
        if '200' not in resp.split('\r\n')[0]:
            return False, f'PLAY失败'

        print(f"[RTSP-Range] PLAY成功, 开始接收RTP数据...")

        # Step 6: 接收RTP数据，解析提取H.264 NAL单元，写入临时文件
        h264_path = output_path.with_suffix('.h264')

        rtp_buf = b''
        total_bytes = 0
        h264_bytes = 0
        start_wait = time.time()
        nal_types_seen = set()

        empty_count = 0
        recv_count = 0
        with open(h264_path, 'wb') as h264_f:
            while time.time() - start_wait < max_wait:
                try:
                    data = sock.recv(65536)
                    if not data:
                        empty_count += 1
                        elapsed = time.time() - start_wait
                        print(f"[RTSP-Range] 连接空读 #{empty_count}, 已接收{elapsed:.0f}秒, h264={h264_bytes}字节")
                        if empty_count >= 3:
                            print(f"[RTSP-Range] NVR连续3次空读，停止接收")
                            break
                        time.sleep(1)
                        continue
                    empty_count = 0
                    recv_count += 1
                    if recv_count % 500 == 0:
                        elapsed = time.time() - start_wait
                        print(f"[RTSP-Range] 接收中: {elapsed:.0f}秒, rtp={total_bytes}, h264={h264_bytes}")
                    rtp_buf += data
                except socket.timeout:
                    elapsed = time.time() - start_wait
                    print(f"[RTSP-Range] socket timeout, 已接收{elapsed:.0f}秒")
                    continue

                # 解析RTSP interleaved数据
                while len(rtp_buf) >= 4:
                    if rtp_buf[0:1] == b'$':
                        # Interleaved frame: $ + channel + length(2 bytes)
                        if len(rtp_buf) < 4:
                            break
                        channel = rtp_buf[1]
                        pkt_len = (rtp_buf[2] << 8) | rtp_buf[3]
                        if len(rtp_buf) < 4 + pkt_len:
                            break
                        rtp_packet = rtp_buf[4:4 + pkt_len]
                        rtp_buf = rtp_buf[4 + pkt_len:]

                        # 只处理RTP数据通道(channel 0)，跳过RTCP(channel 1)
                        if channel == 0 and len(rtp_packet) >= 12:
                            rtp_b0 = rtp_packet[0]
                            padding_flag = (rtp_b0 >> 5) & 1
                            extension_flag = (rtp_b0 >> 4) & 1
                            cc = rtp_b0 & 0x0F
                            header_len = 12 + cc * 4
                            # 跳过扩展头
                            if extension_flag and len(rtp_packet) > header_len + 4:
                                ext_word_count = (rtp_packet[header_len + 2] << 8) | rtp_packet[header_len + 3]
                                header_len += 4 + ext_word_count * 4
                            # 计算payload长度（减去padding）
                            payload_end = len(rtp_packet)
                            if padding_flag and len(rtp_packet) > 0:
                                pad_len = rtp_packet[-1]
                                if pad_len > 0 and pad_len <= payload_end - header_len:
                                    payload_end -= pad_len
                            if payload_end > header_len:
                                payload = rtp_packet[header_len:payload_end]
                                if len(payload) < 1:
                                    continue

                                nal_header = payload[0]
                                nal_type = nal_header & 0x1F
                                nal_types_seen.add(nal_type)

                                if 1 <= nal_type <= 23:
                                    # Single NAL unit (标准H.264)
                                    h264_f.write(b'\x00\x00\x00\x01' + payload)
                                    h264_bytes += 4 + len(payload)
                                elif nal_type == 28:
                                    # FU-A (Fragmentation Unit)
                                    if len(payload) >= 2:
                                        fu_header = payload[1]
                                        start_bit = (fu_header >> 7) & 1
                                        nal_type_orig = fu_header & 0x1F
                                        if start_bit:
                                            # FU-A start: 写入start code + 重建的NAL头 + payload
                                            reconstructed_nal = bytes([(nal_header & 0xE0) | nal_type_orig])
                                            h264_f.write(b'\x00\x00\x00\x01' + reconstructed_nal + payload[2:])
                                            h264_bytes += 4 + 1 + len(payload) - 2
                                        else:
                                            # FU-A continuation/end: 只写payload数据
                                            h264_f.write(payload[2:])
                                            h264_bytes += len(payload) - 2
                                elif nal_type == 24:
                                    # STAP-A (Single-Time Aggregation)
                                    offset = 1
                                    while offset + 2 <= len(payload):
                                        nal_size = (payload[offset] << 8) | payload[offset + 1]
                                        offset += 2
                                        if offset + nal_size <= len(payload):
                                            h264_f.write(b'\x00\x00\x00\x01' + payload[offset:offset + nal_size])
                                            h264_bytes += 4 + nal_size
                                        offset += nal_size
                                # nal_type == 0: 海康威视元数据包，跳过
                                # 其他未知类型也跳过

                        total_bytes += pkt_len
                    elif rtp_buf[0:1] in (b'R', b'S', b'D', b'T', b'P', b'O', b'I'):
                        # RTSP响应消息（如录制结束后的NOTIFY），跳过
                        end_idx = rtp_buf.find(b'\r\n\r\n')
                        if end_idx >= 0:
                            rtp_buf = rtp_buf[end_idx + 4:]
                        else:
                            break
                    else:
                        # 未知数据，跳过一个字节
                        rtp_buf = rtp_buf[1:]

        sock.close()
        sock = None

        elapsed = time.time() - start_wait
        print(f"[RTSP-Range] RTP接收完成: 耗时{elapsed:.0f}秒, rtp={total_bytes}, h264={h264_bytes}, nal_types={sorted(nal_types_seen)}")

        if h264_bytes < 1000:
            try:
                h264_path.unlink()
            except:
                pass
            return False, f'H.264数据不足: {h264_bytes} bytes'

        # Step 7: 用ffmpeg将H.264文件转换为MP4
        # 先用 -c copy 快速封装
        ffmpeg_cmd = [
            'ffmpeg',
            '-loglevel', 'warning',
            '-f', 'h264',
            '-i', str(h264_path),
            '-c', 'copy',
            '-movflags', '+faststart',
            '-y',
            str(output_path),
        ]

        print(f"[RTSP-Range] ffmpeg转换H.264到MP4 (copy模式)...")
        result = subprocess.run(ffmpeg_cmd, capture_output=True, timeout=120)

        # 检查生成的视频时长，如果比请求的短很多，说明NVR丢帧了，需要重编码修正
        if output_path.exists() and duration > 0:
            probe = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(output_path)],
                capture_output=True, text=True, timeout=10
            )
            try:
                actual_duration = float(probe.stdout.strip())
            except (ValueError, AttributeError):
                actual_duration = 0

            if actual_duration > 0 and actual_duration < duration * 0.7:
                # 时长不足请求的70%，NVR丢帧了，重编码修正
                # 用实际帧数和请求时长计算输入帧率
                frame_count_probe = subprocess.run(
                    ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames',
                     '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', str(output_path)],
                    capture_output=True, text=True, timeout=120
                )
                try:
                    frame_count = int(frame_count_probe.stdout.strip())
                except (ValueError, AttributeError):
                    frame_count = int(actual_duration * 25)
                input_fps = frame_count / duration if duration > 0 else 1
                input_fps = max(0.5, min(input_fps, 25))
                print(f"[RTSP-Range] 时长不足({actual_duration:.0f}s < {duration}s, {frame_count}帧), 重编码: input_fps={input_fps:.2f}")
                ffmpeg_reencode = [
                    'ffmpeg',
                    '-loglevel', 'warning',
                    '-r', f'{input_fps:.4f}',
                    '-f', 'h264',
                    '-i', str(h264_path),
                    '-r', '25',
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-movflags', '+faststart',
                    '-y',
                    str(output_path),
                ]
                result = subprocess.run(ffmpeg_reencode, capture_output=True, timeout=600)

        # 清理临时h264文件
        try:
            h264_path.unlink()
        except:
            pass

        if result.returncode != 0:
            stderr = result.stderr.decode('utf-8', errors='replace')
            print(f"[RTSP-Range] ffmpeg失败: {stderr[:300]}")
            return False, f'ffmpeg转换失败: {stderr[:200]}'

        if not output_path.exists() or output_path.stat().st_size < 10000:
            return False, '生成文件无效'

        print(f"[RTSP-Range] 下载成功: {output_path.name}, size={output_path.stat().st_size}")
        return True, None

    except Exception as e:
        logger.error(f"RTSP Range下载失败: {e}")
        print(f"[RTSP-Range] 异常: {e}")
        return False, str(e)
    finally:
        if sock:
            try:
                sock.close()
            except:
                pass


def _try_ffmpeg_mp4(rtsp_url, output_path, duration, max_wait=120):
    """尝试用FFmpeg将RTSP下载为MP4（直接连接，无时间控制）"""
    ffmpeg_cmd = [
        'ffmpeg',
        '-loglevel', 'warning',
        '-rtsp_transport', 'tcp',
        '-i', rtsp_url,
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

        last_error = None
        for i, rtsp_url in enumerate(rtsp_urls):
            # 直接下载到 videos 目录
            video_path = _get_video_cache_path(start_time, end_time, camera_index)
            video_path.parent.mkdir(parents=True, exist_ok=True)

            max_wait = duration + 30  # 时长 + 30秒缓冲
            success, error = _try_ffmpeg_mp4(rtsp_url, video_path, duration, max_wait=max_wait)
            if success:
                print(f"[FFmpeg] 视频下载完成: {video_path}")
                return self._build_response(request, video_path.name, camera, False, is_cached=False)

            if error:
                last_error = error
                print(f"[FFmpeg] URL {i+1} 失败: {error}")

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
