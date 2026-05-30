import React, { useState, useRef, useEffect } from 'react';
import { Modal, Spin, message } from 'antd';
import { VideoCameraOutlined } from '@ant-design/icons';
import { video as videoApi } from '@/api/globApi';
import Hls from 'hls.js';

const VideoPlayer = ({ startTime, endTime, cameraIndex = 0 }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [streamUrl, setStreamUrl] = useState(null);
  const [videoError, setVideoError] = useState(null);
  const [videoLoading, setVideoLoading] = useState(false);
  const [videoEl, setVideoEl] = useState(null);
  const videoRef = useRef(null);
  const hlsRef = useRef(null);

  const destroyHls = () => {
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }
  };

  const playHls = (url) => {
    const video = videoEl;
    if (!video) return;

    destroyHls();

    // Safari
    if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = url;
      video.addEventListener('loadedmetadata', () => {
        setVideoLoading(false);
        video.play().catch(() => {});
      }, { once: true });
      video.addEventListener('error', () => {
        setVideoError('视频加载失败');
        setVideoLoading(false);
      }, { once: true });
      return;
    }

    // hls.js
    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        fragLoadingTimeOut: 30000,
        manifestLoadingTimeOut: 30000,
      });
      hlsRef.current = hls;
      hls.loadSource(url);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setVideoLoading(false);
        video.play().catch(() => {});
      });
      hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
          const msg = data.type === 'networkError' ? '网络连接失败，请检查摄像头' : '视频格式错误';
          setVideoError(msg);
          setVideoLoading(false);
        }
      });
      return;
    }

    setVideoError('当前浏览器不支持视频播放，请使用Chrome或Safari');
    setVideoLoading(false);
  };

  useEffect(() => {
    // 当弹窗关闭时清理
    if (!modalOpen) {
      destroyHls();
      setVideoLoading(false);
      setVideoEl(null);
    }
  }, [modalOpen]);

  const handlePlay = async () => {
    if (!startTime || !endTime) {
      message.warning('该记录没有录像时间段');
      return;
    }
    setLoading(true);
    setVideoError(null);
    destroyHls();
    try {
      // 使用较长的超时时间，等待HLS转换完成
      const res = await videoApi.getStreamUrl({
        start_time: startTime,
        end_time: endTime,
        camera: cameraIndex,
      }, 20000); // 20秒超时
      if (res?.url) {
        setStreamUrl(res.url);
        setModalOpen(true);
        setVideoLoading(true);
      } else {
        message.error('获取播放地址失败');
        setLoading(false);
      }
    } catch (error) {
      console.error('获取视频流失败', error);
      const errMsg = error?.response?.data?.msg || error.message || '未知错误';
      if (errMsg.includes('timeout') || errMsg.includes('超时')) {
        message.error('连接摄像头超时，请检查摄像头状态');
      } else {
        message.error('获取播放地址失败: ' + errMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setModalOpen(false);
    setTimeout(() => {
      destroyHls();
      setStreamUrl(null);
      setVideoError(null);
      setVideoLoading(false);
    }, 100);
  };

  return (
    <>
      <div
        onClick={handlePlay}
        style={{
          width: 36,
          height: 36,
          borderRadius: 4,
          background: 'rgba(0, 240, 255, 0.1)',
          border: '1px solid rgba(0, 240, 255, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          margin: '0 auto',
        }}
      >
        {loading ? (
          <Spin size="small" />
        ) : (
          <VideoCameraOutlined style={{ fontSize: 16, color: '#00f0ff' }} />
        )}
      </div>
      <Modal
        title="录像播放"
        open={modalOpen}
        onCancel={handleClose}
        footer={null}
        width={800}
        centered
        destroyOnClose
      >
        <div style={{ position: 'relative', minHeight: 300, background: '#000', borderRadius: 4, overflow: 'hidden' }}>
          {videoLoading && (
            <div style={{
              position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexDirection: 'column', gap: 12, zIndex: 1,
            }}>
              <Spin size="large" />
              <span style={{ color: '#fff' }}>正在加载视频流...</span>
            </div>
          )}
          {videoError && (
            <div style={{
              position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexDirection: 'column', gap: 12, zIndex: 1,
            }}>
              <span style={{ color: '#ff4d4f', fontSize: 16 }}>{videoError}</span>
            </div>
          )}
          {streamUrl && (
            <video
              ref={(el) => {
                videoRef.current = el;
                setVideoEl(el);
                // video元素挂载后立即尝试播放
                if (el && streamUrl) {
                  playHls(streamUrl);
                }
              }}
              controls
              autoPlay
              style={{ width: '100%', maxHeight: '70vh', display: 'block' }}
            />
          )}
        </div>
      </Modal>
    </>
  );
};

export default VideoPlayer;
