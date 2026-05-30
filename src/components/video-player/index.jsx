import React, { useState, useRef, useEffect } from 'react';
import { Modal, Spin, message } from 'antd';
import { VideoCameraOutlined, ReloadOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { video as videoApi } from '@/api/globApi';
import Hls from 'hls.js';

const VideoPlayer = ({ startTime, endTime, cameraIndex = 0 }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [streamUrl, setStreamUrl] = useState(null);
  const [videoError, setVideoError] = useState(null);
  const [videoLoading, setVideoLoading] = useState(false);
  const [videoEl, setVideoEl] = useState(null);
  const [cameraName, setCameraName] = useState('');
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
      const res = await videoApi.getStreamUrl({
        start_time: startTime,
        end_time: endTime,
        camera: cameraIndex,
      }, 20000);
      if (res?.url) {
        setStreamUrl(res.url);
        setCameraName(res.camera_name || `摄像头 ${cameraIndex + 1}`);
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

  const formatTime = (t) => {
    if (!t) return '';
    return t.replace('T', ' ').replace('Z', '');
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
          transition: 'all 0.2s',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'rgba(0, 240, 255, 0.2)';
          e.currentTarget.style.borderColor = 'rgba(0, 240, 255, 0.5)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'rgba(0, 240, 255, 0.1)';
          e.currentTarget.style.borderColor = 'rgba(0, 240, 255, 0.3)';
        }}
      >
        {loading ? (
          <Spin size="small" />
        ) : (
          <VideoCameraOutlined style={{ fontSize: 16, color: '#00f0ff' }} />
        )}
      </div>
      <Modal
        title={
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            color: '#fff',
          }}>
            <VideoCameraOutlined style={{ color: '#00f0ff' }} />
            <span>录像播放</span>
          </div>
        }
        open={modalOpen}
        onCancel={handleClose}
        footer={null}
        width={860}
        centered
        destroyOnClose
        className="video-modal"
        styles={{
          content: {
            background: '#1a1a2e',
            borderRadius: 8,
            padding: 0,
            overflow: 'hidden',
          },
          header: {
            background: '#16213e',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
            padding: '12px 16px',
            margin: 0,
          },
        }}
      >
        <div style={{
          position: 'relative',
          width: '100%',
          height: 450,
          background: '#0a0a15',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
        }}>
          {/* 视频 */}
          {streamUrl && !videoError && (
            <video
              ref={(el) => {
                videoRef.current = el;
                setVideoEl(el);
                if (el && streamUrl) {
                  playHls(streamUrl);
                }
              }}
              controls
              autoPlay
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                display: videoLoading ? 'none' : 'block',
              }}
            />
          )}

          {/* 加载中 */}
          {videoLoading && (
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#0a0a15',
              zIndex: 3,
            }}>
              <div style={{
                width: 50,
                height: 50,
                borderRadius: '50%',
                border: '3px solid rgba(0, 240, 255, 0.2)',
                borderTopColor: '#00f0ff',
                animation: 'spin 1s linear infinite',
              }} />
              <span style={{ color: '#fff', marginTop: 16, fontSize: 14 }}>正在加载视频流...</span>
              <span style={{ color: 'rgba(255,255,255,0.45)', fontSize: 12, marginTop: 6 }}>
                正在连接摄像头，请稍候
              </span>
            </div>
          )}

          {/* 错误状态 */}
          {videoError && (
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#0a0a15',
              zIndex: 3,
            }}>
              <ExclamationCircleOutlined style={{ fontSize: 44, color: '#ff4d4f' }} />
              <span style={{ color: '#ff4d4f', fontSize: 14, marginTop: 14 }}>{videoError}</span>
              <div
                onClick={handlePlay}
                style={{
                  marginTop: 16,
                  padding: '8px 24px',
                  background: 'rgba(0, 240, 255, 0.08)',
                  border: '1px solid rgba(0, 240, 255, 0.3)',
                  borderRadius: 4,
                  color: '#00f0ff',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  fontSize: 13,
                }}
              >
                <ReloadOutlined />
                重试
              </div>
            </div>
          )}

          {/* 顶部信息栏 */}
          {!videoLoading && !videoError && streamUrl && (
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              padding: '10px 14px',
              background: 'linear-gradient(to bottom, rgba(0,0,0,0.75), transparent)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              zIndex: 2,
              pointerEvents: 'none',
            }}>
              <div style={{ color: 'rgba(255,255,255,0.75)', fontSize: 12 }}>
                <span style={{ marginRight: 14 }}>
                  {startTime && `开始: ${formatTime(startTime)}`}
                </span>
                <span>
                  {endTime && `结束: ${formatTime(endTime)}`}
                </span>
              </div>
              <div style={{ color: '#00f0ff', fontSize: 12 }}>
                {cameraName}
              </div>
            </div>
          )}
        </div>
        {/* 底部控制栏 */}
        <div style={{
          padding: '10px 16px',
          background: '#16213e',
          borderTop: '1px solid rgba(255,255,255,0.1)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 12 }}>
            RTSP流媒体服务 · HLS播放
          </div>
        </div>
      </Modal>
      <style>{`
        .video-modal .ant-modal-close-icon {
          color: rgba(255,255,255,0.8) !important;
        }
        .video-modal .ant-modal-close:hover .ant-modal-close-icon {
          color: #fff !important;
        }
      `}</style>
    </>
  );
};

export default VideoPlayer;