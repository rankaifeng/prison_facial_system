#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RTSP 转 MP4 录制工具

支持两种场景：
  1. 回放流（URL 带 starttime/endtime）—— 自动解析时长，用 -t 让 ffmpeg 精确停止
  2. 实时流 —— 通过 --duration 指定录制时长，或等待手动停止

特性：
  - 自动解析 URL 中的 starttime/endtime 计算录制时长（海康/大华回放流）
  - TCP 传输，避免 UDP 丢包
  - -c copy 直接拷贝流，不转码，速度快、无损
  - faststart 优化，MP4 支持网页渐进式播放
  - 连通性预检（ffprobe），提前发现认证/网络问题
  - 停滞检测：回放流播完后 NVR 不关连接时，主动收尾
  - 管道安全排空：SIGINT 后正确排空 stderr，防止死锁导致 MP4 尾部丢失
  - 可作为命令行工具，也可作为模块导入（供 Django/DRF 调用）

用法：
  # 回放流（自动解析 starttime/endtime，自动结束）
  python rtsp_to_mp4.py \
      "rtsp://admin:root123a@192.168.100.150/Streaming/tracks/1601/?starttime=20260618T121853Z&endtime=20260618T122002Z" \
      -o ./playback.mp4

  # 实时流，录 60 秒
  python rtsp_to_mp4.py \
      "rtsp://admin:root123a@192.168.100.150/cam/realmonitor?channel=1&subtype=0" \
      -o ./live.mp4 -d 60

  # 作为模块调用
  from rtsp_to_mp4 import record_rtsp_to_mp4
  record_rtsp_to_mp4(
      rtsp_url="rtsp://admin:root123a@192.168.100.150/Streaming/tracks/1601/?...",
      output_path="./playback.mp4",
  )
"""

import argparse
import json
import os
import re
import select
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# ──────────────────────────── 工具函数 ────────────────────────────

def _check_ffmpeg():
    """确认 ffmpeg / ffprobe 可用"""
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise EnvironmentError(f"未找到 {tool}，请先安装 ffmpeg（含 ffprobe）")


def parse_playback_duration(rtsp_url: str):
    """
    从 RTSP URL 中解析 starttime/endtime，计算回放时长（秒）。

    海康/大华回放流 URL 格式：
      ...?starttime=20260618T121853Z&endtime=20260618T122002Z

    返回 (duration_seconds: float|None, info: str|None)
    """
    m_start = re.search(r'starttime=(\d{8}T\d{6}Z)', rtsp_url, re.IGNORECASE)
    m_end = re.search(r'endtime=(\d{8}T\d{6}Z)', rtsp_url, re.IGNORECASE)
    if not m_start or not m_end:
        return None, None

    fmt = "%Y%m%dT%H%M%SZ"
    try:
        start_dt = datetime.strptime(m_start.group(1), fmt)
        end_dt = datetime.strptime(m_end.group(1), fmt)
        delta = (end_dt - start_dt).total_seconds()
        if delta > 0:
            return delta, f"{m_start.group(1)} → {m_end.group(1)}"
    except ValueError:
        pass
    return None, None


def probe_stream(rtsp_url: str, timeout: int = 15):
    """
    用 ffprobe 探测 RTSP 流信息，做连通性预检。

    返回 (ok: bool, info: dict|str)
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-rtsp_transport", "tcp",
        "-show_entries",
        "stream=codec_name,codec_type,width,height,r_frame_rate"
        ":format=duration,format_name",
        "-of", "json",
        rtsp_url,
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout + 5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return True, json.loads(result.stdout)
        return False, (result.stderr.strip() or result.stdout.strip()
                       or "探测失败（未知原因）")
    except subprocess.TimeoutExpired:
        return False, f"探测超时（{timeout}s）—— 设备可能不可达或认证失败"
    except json.JSONDecodeError:
        return False, "探测返回非 JSON，流可能不正常"
    except Exception as e:
        return False, f"探测异常: {e}"


def _parse_progress(line: str) -> dict:
    """解析 ffmpeg stderr 的一行，提取已录制时长（秒）和速度"""
    info = {}
    m = re.search(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)", line)
    if m:
        h, mm, ss = m.groups()
        info["elapsed"] = int(h) * 3600 + int(mm) * 60 + float(ss)
    m = re.search(r"speed=\s*([\d.]+)x", line)
    if m:
        info["speed"] = float(m.group(1))
    return info


def _fmt_seconds(s: float) -> str:
    h = int(s) // 3600
    m = (int(s) % 3600) // 60
    sec = s - h * 3600 - m * 60
    if h:
        return f"{h:d}:{m:02d}:{sec:05.2f}"
    return f"{m:02d}:{sec:05.2f}"


def verify_mp4(path: str) -> tuple:
    """
    验证本地 MP4 文件是否可正常播放（有视频流且能读到时长）。

    返回 (ok: bool, info: str)
    """
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "stream=codec_type,duration"
             ":format=duration",
             "-of", "json", path],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode == 0 and r.stdout.strip():
            data = json.loads(r.stdout)
            streams = data.get("streams", [])
            has_video = any(s.get("codec_type") == "video" for s in streams)
            dur = float(data.get("format", {}).get("duration") or 0)
            if has_video and dur > 0:
                return True, f"视频有效，时长 {_fmt_seconds(dur)}"
            if has_video and dur <= 0:
                return False, "视频时长为0（moov atom 不完整）"
            return False, "无视频流"
        return False, (r.stderr.strip() or "文件损坏，无法解析")
    except Exception as e:
        return False, f"验证异常: {e}"


def _drain_and_wait(proc: subprocess.Popen, timeout: float = 60,
                    log_lines: list = None) -> int:
    """
    排空 stderr 管道并等待进程退出。

    解决 proc.wait() 与 stderr PIPE 的死锁问题：
    当 ffmpeg 的 stderr 管道缓冲区写满时，ffmpeg 会阻塞在 write() 上，
    无法退出并写 MP4 尾部（moov atom）。此函数持续读取 stderr 直到进程退出。

    返回进程退出码。
    """
    if log_lines is None:
        log_lines = []

    fd = proc.stderr.fileno()
    deadline = time.time() + timeout

    while time.time() < deadline:
        # 1 秒超时检查是否有数据可读
        try:
            ready, _, _ = select.select([fd], [], [], 1.0)
        except (OSError, ValueError):
            break

        if ready:
            line = proc.stderr.readline()
            if not line:
                # EOF — 进程已关闭 stderr，即将退出
                break
            log_lines.append(line.rstrip())
        elif proc.poll() is not None:
            # 进程已退出
            break

    if proc.poll() is None:
        # 超时仍未退出，强制杀死
        proc.kill()

    proc.wait()
    return proc.returncode


# ──────────────────────────── 核心录制 ────────────────────────────

def record_rtsp_to_mp4(
    rtsp_url: str,
    output_path: str,
    duration: float = None,
    timeout: int = 600,
    stall_timeout: int = 30,
    overwrite: bool = False,
    pre_probe: bool = True,
    verbose: bool = True,
    debug: bool = False,
) -> dict:
    """
    将 RTSP 流录制为本地 MP4 文件。

    参数:
      rtsp_url     : RTSP 地址（可带 starttime/endtime 回放参数）
      output_path  : 输出 MP4 路径
      duration     : 录制时长（秒）。None 时自动从 URL 解析 starttime/endtime
      timeout      : 最大等待超时（秒），防止设备掉线挂死
      stall_timeout: 进度停滞超时（秒）。time= 连续 N 秒不增长则主动收尾。
                     设 0 禁用（仅当 -t 未生效时的后备机制）
      overwrite    : 是否覆盖已存在的输出文件
      pre_probe    : 录制前是否用 ffprobe 预检连通性
      verbose      : 是否打印进度日志
      debug        : 调试模式，打印完整 ffmpeg 命令

    返回:
      dict: { success, output, size, elapsed, message }
    """
    _check_ffmpeg()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "success": False,
        "output": str(output),
        "size": 0,
        "elapsed": 0.0,
        "message": "",
    }

    # ── 1. 解析录制时长 ──
    auto_duration = None
    if duration is None:
        auto_duration, time_info = parse_playback_duration(rtsp_url)
        if auto_duration is not None:
            duration = auto_duration
            if verbose:
                print(f"[分析] 检测到回放时间段: {time_info}")
                print(f"[分析] 计算时长: {_fmt_seconds(duration)}")

    # ── 2. 连通性预检 ──
    if pre_probe:
        if verbose:
            print(f"[预检] 正在探测流: {rtsp_url.split('@')[-1]}")
        ok, info = probe_stream(rtsp_url, timeout=15)
        if not ok:
            result["message"] = f"预检失败: {info}"
            if verbose:
                print(f"[预检] ✗ {info}")
            return result
        if verbose:
            streams = info.get("streams", [])
            v = next((s for s in streams if s.get("codec_type") == "video"), None)
            if v:
                print(f"[预检] ✓ 视频: {v.get('codec_name')} "
                      f"{v.get('width')}x{v.get('height')} "
                      f"@ {v.get('r_frame_rate')}")

    # ── 3. 构建 ffmpeg 命令 ──
    cmd = [
        "ffmpeg",
        "-y" if overwrite else "-n",
        "-rtsp_transport", "tcp",
        "-i", rtsp_url,
    ]

    # 录制时长：有 -t 时 ffmpeg 会自然停止并正确写完 MP4 尾部
    has_t = False
    if duration is not None and duration > 0:
        cmd += ["-t", str(duration)]
        has_t = True

    cmd += [
        "-an",
        "-c", "copy",
        "-f", "mp4",
        "-fflags", "+genpts",
        "-avoid_negative_ts", "make_zero",
        str(output),
    ]

    if verbose:
        print(f"[录制] 开始 -> {output}")
        if has_t:
            print(f"[录制] 策略: 固定时长 {_fmt_seconds(duration)}（ffmpeg 自然停止）")
        else:
            print(f"[录制] 策略: 等待流自然结束（停滞检测后备）")
        print(f"[录制] 超时保护: {timeout}s")
    if debug:
        cmd_display = " ".join(f'"{a}"' if (" " in a or "&" in a) else a for a in cmd)
        print(f"[DEBUG] ffmpeg 命令:\n{cmd_display}")

    # ── 4. 启动 ffmpeg，实时读取进度 ──
    start = time.time()
    last_print = 0.0
    log_lines = []

    # 停滞检测状态
    last_progress_time = None      # 上一次解析到的 time= 值（秒）
    last_progress_wall = None      # 上一次 time= 更新时的墙钟时间
    stall_triggered = False

    try:
        proc = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        try:
            while True:
                line = proc.stderr.readline()
                if not line:
                    if proc.poll() is not None:
                        break
                    continue

                log_lines.append(line.rstrip())

                # 解析进度
                prog = _parse_progress(line)
                now = time.time()

                # 更新停滞检测基准
                if prog and "elapsed" in prog:
                    cur_t = prog["elapsed"]
                    if last_progress_time is None or abs(cur_t - last_progress_time) > 0.01:
                        last_progress_time = cur_t
                        last_progress_wall = now

                # 停滞检测（仅当未设 -t 时启用，或 -t 未生效时的后备）
                if (stall_timeout > 0
                        and last_progress_wall is not None
                        and last_progress_time is not None
                        and last_progress_time > 3.0
                        and (now - last_progress_wall) > stall_timeout
                        and not stall_triggered):
                    stall_triggered = True
                    if verbose:
                        print(f"[录制] 流已播完（time={_fmt_seconds(last_progress_time)} "
                              f"连续 {stall_timeout}s 无新数据），正在收尾...")
                    proc.send_signal(signal.SIGINT)
                    # 关键：排空 stderr 管道，防止 ffmpeg 阻塞在 write() 上无法退出
                    # 否则 MP4 尾部（moov atom）不会被写入，文件打不开
                    # 大文件需要更多时间写 moov atom，默认等 60 秒
                    _drain_and_wait(proc, timeout=60, log_lines=log_lines)
                    break

                # 进度打印
                if verbose and prog and (now - last_print >= 1.0):
                    elapsed_val = prog.get("elapsed", now - start)
                    msg = f"[录制] 已录 {_fmt_seconds(elapsed_val)}"
                    if "speed" in prog:
                        msg += f"  速度 {prog['speed']}x"
                    # 停滞时降低打印频率
                    if (last_progress_wall is not None
                            and last_progress_time is not None
                            and (now - last_progress_wall) > 2.0):
                        if (now - last_print) < 5.0:
                            continue  # 停滞期间每 5 秒打印一次
                        msg += "  (等待结束...)"
                    print(msg, flush=True)
                    last_print = now

                # 最大超时保护
                if (now - start) > timeout:
                    proc.terminate()
                    _drain_and_wait(proc, timeout=30, log_lines=log_lines)
                    result["message"] = f"达到最大超时 {timeout}s，已终止"
                    if verbose:
                        print(f"[录制] ! {result['message']}")
                    break

            if not stall_triggered and proc.poll() is None:
                proc.wait(timeout=10)
        except KeyboardInterrupt:
            if verbose:
                print("\n[录制] 收到中断信号，优雅停止 ffmpeg ...")
            proc.send_signal(signal.SIGINT)
            _drain_and_wait(proc, timeout=15, log_lines=log_lines)

    except Exception as e:
        result["message"] = f"录制异常: {e}"
        if verbose:
            print(f"[录制] ✗ {result['message']}")
        return result

    # ── 5. 检查结果 ──
    result["elapsed"] = time.time() - start
    rc = proc.returncode

    if output.exists() and output.stat().st_size > 0:
        size = output.stat().st_size
        result["size"] = size

        # 诊断：输出 ffprobe 完整信息
        if verbose:
            try:
                diag = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries",
                     "stream=codec_type,codec_name,duration,nb_frames,width,height,r_frame_rate"
                     ":format=duration,size,nb_streams",
                     "-of", "json", str(output)],
                    capture_output=True, text=True, timeout=15,
                )
                print(f"[诊断] ffprobe 输出:\n{diag.stdout.strip()}")
                if diag.stderr.strip():
                    print(f"[诊断] ffprobe 错误:\n{diag.stderr.strip()}")
            except Exception as e:
                print(f"[诊断] ffprobe 异常: {e}")

        ok, vinfo = verify_mp4(str(output))
        if ok:
            result["success"] = True
            if rc == 0 and not stall_triggered:
                result["message"] = "录制完成"
            else:
                tag = "流播完收尾" if stall_triggered else "设备断开"
                result["message"] = f"录制完成（{tag}，返回码 {rc}，{vinfo}）"
        else:
            result["message"] = f"录制失败（返回码 {rc}，文件不完整: {vinfo}）"

        if verbose:
            size_kb = size / 1024
            size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
            tag = "✓" if result["success"] else "✗"
            print(f"[完成] {tag} {output}")
            print(f"       大小: {size_str}  耗时: {result['elapsed']:.1f}s  "
                  f"返回码: {rc}")
            if result["success"] and rc != 0:
                print(f"       备注: {result['message']}")
            if not result["success"] and log_lines:
                tail = log_lines[-20:]
                print(f"[诊断] ffmpeg 日志最后 {len(tail)} 行:")
                for l in tail:
                    if l.strip():
                        print(f"  {l}")
    else:
        result["message"] = result["message"] or f"录制失败（返回码 {rc}）"
        if verbose:
            print(f"[完成] ✗ {result['message']}")
            if log_lines:
                tail = log_lines[-20:]
                print(f"[诊断] ffmpeg 日志最后 {len(tail)} 行:")
                for l in tail:
                    if l.strip():
                        print(f"  {l}")

    return result


# ──────────────────────────── 命令行入口 ────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="RTSP 转 MP4 录制工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 回放流（自动解析 starttime/endtime，自动结束）
  %(prog)s "rtsp://admin:pass@192.168.1.100/Streaming/tracks/1601/?starttime=...&endtime=..." -o out.mp4

  # 实时流录 60 秒
  %(prog)s "rtsp://admin:pass@192.168.1.100/cam/realmonitor?channel=1&subtype=0" -o live.mp4 -d 60

  # 跳过预检直接录
  %(prog)s "rtsp://..." -o out.mp4 --no-probe
        """,
    )
    ap.add_argument("url", help="RTSP 地址")
    ap.add_argument("-o", "--output", default=None,
                    help="输出 MP4 路径（默认 ./recordings/<时间戳>.mp4）")
    ap.add_argument("-d", "--duration", type=float, default=None,
                    help="录制时长（秒）。留空则自动从 URL 解析 starttime/endtime")
    ap.add_argument("-t", "--timeout", type=int, default=600,
                    help="最大超时保护秒数（默认 600）")
    ap.add_argument("--stall-timeout", type=int, default=8,
                    help="进度停滞超时秒数（默认 8）。设 0 禁用")
    ap.add_argument("--overwrite", action="store_true",
                    help="覆盖已存在文件")
    ap.add_argument("--no-probe", action="store_true",
                    help="跳过预检")
    ap.add_argument("--debug", action="store_true",
                    help="调试模式：打印完整 ffmpeg 命令")
    ap.add_argument("-q", "--quiet", action="store_true",
                    help="静默模式")
    args = ap.parse_args()

    output = args.output
    if not output:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = os.path.join("recordings", f"{ts}.mp4")

    res = record_rtsp_to_mp4(
        rtsp_url=args.url,
        output_path=output,
        duration=args.duration,
        timeout=args.timeout,
        stall_timeout=args.stall_timeout,
        overwrite=args.overwrite,
        pre_probe=not args.no_probe,
        verbose=not args.quiet,
        debug=args.debug,
    )

    sys.exit(0 if res["success"] else 1)


if __name__ == "__main__":
    main()
