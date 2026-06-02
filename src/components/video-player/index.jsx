import React, { useState, useRef, useEffect, useCallback } from 'react';
import { VideoCameraOutlined, ReloadOutlined, ExpandOutlined, CompressOutlined } from '@ant-design/icons';

const VideoPlayer = ({ itemData }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const videoRef = useRef(null);
  const controlsTimeoutRef = useRef(null);
  const modalRef = useRef(null);

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '00:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  const getDateTimeString = () => {
    const now = new Date();
    return now.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).replace(/\//g, '-');
  };

  const handleMouseMove = useCallback(() => {
    setShowControls(true);
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
    if (isPlaying) {
      controlsTimeoutRef.current = setTimeout(() => {
        setShowControls(false);
      }, 3000);
    }
  }, [isPlaying]);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      modalRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  const handlePlayPause = useCallback(() => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
    }
  }, [isPlaying]);

  const handleRestart = useCallback(() => {
    if (videoRef.current) {
      videoRef.current.currentTime = 0;
      videoRef.current.play();
    }
  }, []);

  const handleSeek = useCallback((e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    if (videoRef.current && videoRef.current.duration) {
      videoRef.current.currentTime = percentage * videoRef.current.duration;
    }
  }, []);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  useEffect(() => {
    return () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!modalOpen) return;
      if (e.key === 'Escape') setModalOpen(false);
      if (e.key === ' ') { e.preventDefault(); handlePlayPause(); }
      if (e.key === 'ArrowLeft') {
        if (videoRef.current) videoRef.current.currentTime -= 5;
      }
      if (e.key === 'ArrowRight') {
        if (videoRef.current) videoRef.current.currentTime += 5;
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [modalOpen, handlePlayPause]);

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  if (!itemData?.video_url) {
    return (
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: 4,
          background: 'rgba(225, 29, 72, 0.1)',
          border: '1px solid rgba(225, 29, 72, 0.25)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'not-allowed',
          margin: '0 auto',
          opacity: 0.5,
        }}
        title="暂无录像"
      >
        <VideoCameraOutlined style={{ fontSize: 16, color: '#E11D48' }} />
      </div>
    );
  }

  return (
    <>
      {/* Trigger Button */}
      <div
        onClick={() => setModalOpen(true)}
        style={{
          width: 36,
          height: 36,
          borderRadius: 6,
          background: 'linear-gradient(135deg, #1E1B4B 0%, #0F0F23 100%)',
          border: '1px solid rgba(139, 92, 246, 0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          margin: '0 auto',
          position: 'relative',
          overflow: 'hidden',
          transition: 'all 0.25s ease',
          boxShadow: '0 0 20px rgba(139, 92, 246, 0.15)',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.08)';
          e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.7)';
          e.currentTarget.style.boxShadow = '0 0 30px rgba(139, 92, 246, 0.3)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.4)';
          e.currentTarget.style.boxShadow = '0 0 20px rgba(139, 92, 246, 0.15)';
        }}
      >
        {/* Subtle gradient overlay */}
        <div style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, transparent 100%)',
          opacity: 0.5,
        }} />
        <VideoCameraOutlined style={{ fontSize: 15, color: '#A78BFA', position: 'relative', zIndex: 1 }} />
      </div>

      {/* Modal */}
      {modalOpen && (
        <div
          ref={modalRef}
          onMouseMove={handleMouseMove}
          onClick={(e) => {
            if (e.target === e.currentTarget) setModalOpen(false);
          }}
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0, 0, 0, 0.92)',
            backdropFilter: 'blur(8px)',
            animation: 'fadeIn 0.2s ease-out',
          }}
        >
          <style>{`
            @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap');

            @keyframes fadeIn {
              from { opacity: 0; transform: scale(0.98); }
              to { opacity: 1; transform: scale(1); }
            }
            @keyframes borderPulse {
              0%, 100% { box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.3), 0 0 30px rgba(139, 92, 246, 0.1); }
              50% { box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.5), 0 0 40px rgba(139, 92, 246, 0.2); }
            }
            @keyframes recBlink {
              0%, 100% { opacity: 1; }
              50% { opacity: 0.3; }
            }
            .video-container {
              animation: borderPulse 3s ease-in-out infinite;
            }
            .progress-track {
              cursor: pointer;
            }
            .progress-track:hover .progress-fill {
              height: 6px;
            }
            .progress-track:hover .progress-thumb {
              opacity: 1;
              transform: translateX(-50%) scale(1);
            }
            .control-btn:hover {
              background: rgba(139, 92, 246, 0.2) !important;
              border-color: rgba(139, 92, 246, 0.6) !important;
            }
            .control-btn:hover svg {
              color: #A78BFA !important;
            }
          `}</style>

          {/* Video Container */}
          <div
            className="video-container"
            style={{
              position: 'relative',
              width: isFullscreen ? '100vw' : 'min(92vw, 1100px)',
              height: isFullscreen ? '100vh' : 'auto',
              aspectRatio: isFullscreen ? 'unset' : '16 / 9',
              background: '#000',
              borderRadius: isFullscreen ? 0 : 12,
              overflow: 'hidden',
            }}
          >
            {/* Video Element */}
            <video
              ref={videoRef}
              src={itemData?.video_url}
              onClick={handlePlayPause}
              onTimeUpdate={() => {
                if (videoRef.current) {
                  setCurrentTime(videoRef.current.currentTime);
                }
              }}
              onLoadedMetadata={() => {
                if (videoRef.current) {
                  setDuration(videoRef.current.duration);
                }
              }}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                cursor: 'pointer',
                display: 'block',
              }}
            />

            {/* Top Overlay */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                padding: isFullscreen ? '24px 32px' : '20px 24px',
                background: 'linear-gradient(to bottom, rgba(0,0,0,0.75) 0%, transparent 100%)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                pointerEvents: 'none',
                opacity: showControls ? 1 : 0,
                transition: 'opacity 0.3s ease',
              }}
            >
              {/* Left Info */}
              <div>
                <div style={{
                  fontFamily: '"Fira Code", monospace',
                  fontSize: 13,
                  color: '#E11D48',
                  letterSpacing: '0.08em',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginBottom: 6,
                }}>
                  <span style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: '#E11D48',
                    animation: 'recBlink 1s ease-in-out infinite',
                    boxShadow: '0 0 8px #E11D48',
                  }} />
                  {getDateTimeString()}
                </div>
                <div style={{
                  fontFamily: '"Fira Code", monospace',
                  fontSize: 11,
                  color: 'rgba(255, 255, 255, 0.45)',
                  letterSpacing: '0.04em',
                }}>
                  CAM-{String(itemData?.prisoner_no || '001').padStart(3, '0')} · {itemData?.prison_area_name || '监区'} · {itemData?.camera_name || '出监摄像头'}
                </div>
              </div>

              {/* Right Time Range */}
              <div style={{
                fontFamily: '"Fira Code", monospace',
                fontSize: 11,
                color: 'rgba(255, 255, 255, 0.35)',
                textAlign: 'right',
              }}>
                {itemData?.start_time && itemData?.end_time && (
                  <div>{itemData.start_time}</div>
                )}
                {itemData?.start_time && itemData?.end_time && (
                  <div style={{ opacity: 0.6 }}>{itemData.end_time}</div>
                )}
              </div>
            </div>

            {/* Center Play Button (when paused) */}
            {!isPlaying && (
              <div
                onClick={handlePlayPause}
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: 72,
                  height: 72,
                  borderRadius: '50%',
                  background: 'rgba(15, 15, 35, 0.85)',
                  border: '1px solid rgba(139, 92, 246, 0.5)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  backdropFilter: 'blur(12px)',
                  transition: 'all 0.25s ease',
                  boxShadow: '0 0 40px rgba(139, 92, 246, 0.25)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translate(-50%, -50%) scale(1.1)';
                  e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.8)';
                  e.currentTarget.style.boxShadow = '0 0 60px rgba(139, 92, 246, 0.4)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translate(-50%, -50%) scale(1)';
                  e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.5)';
                  e.currentTarget.style.boxShadow = '0 0 40px rgba(139, 92, 246, 0.25)';
                }}
              >
                <div style={{
                  width: 0,
                  height: 0,
                  borderLeft: '20px solid #A78BFA',
                  borderTop: '12px solid transparent',
                  borderBottom: '12px solid transparent',
                  marginLeft: 4,
                  filter: 'drop-shadow(0 0 8px rgba(167, 139, 250, 0.6))',
                }} />
              </div>
            )}

            {/* Bottom Controls */}
            <div
              style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                padding: isFullscreen ? '32px 40px 28px' : '24px 28px 20px',
                background: 'linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 100%)',
                opacity: showControls ? 1 : 0,
                transition: 'opacity 0.3s ease',
              }}
            >
              {/* Progress Bar */}
              <div
                className="progress-track"
                onClick={handleSeek}
                style={{
                  position: 'relative',
                  width: '100%',
                  height: 4,
                  background: 'rgba(255, 255, 255, 0.15)',
                  borderRadius: 2,
                  marginBottom: 16,
                  transition: 'height 0.15s ease',
                }}
              >
                <div
                  className="progress-fill"
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    height: '100%',
                    width: `${progress}%`,
                    background: 'linear-gradient(90deg, #7C3AED 0%, #A78BFA 100%)',
                    borderRadius: 2,
                    transition: 'height 0.15s ease',
                    boxShadow: '0 0 12px rgba(139, 92, 246, 0.5)',
                  }}
                />
                <div
                  className="progress-thumb"
                  style={{
                    position: 'absolute',
                    top: '50%',
                    width: 14,
                    height: 14,
                    borderRadius: '50%',
                    background: '#A78BFA',
                    transform: 'translateX(-50%) translateY(-50%) scale(0)',
                    opacity: 0,
                    transition: 'all 0.15s ease',
                    boxShadow: '0 0 10px rgba(167, 139, 250, 0.8)',
                  }}
                />
              </div>

              {/* Control Buttons */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                {/* Left Controls */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  {/* Play/Pause */}
                  <button
                    className="control-btn"
                    onClick={handlePlayPause}
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 8,
                      background: 'rgba(255, 255, 255, 0.06)',
                      border: '1px solid rgba(255, 255, 255, 0.12)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                    aria-label={isPlaying ? '暂停' : '播放'}
                  >
                    {isPlaying ? (
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <rect x="3" y="2" width="4" height="12" rx="1" fill="#A78BFA" />
                        <rect x="9" y="2" width="4" height="12" rx="1" fill="#A78BFA" />
                      </svg>
                    ) : (
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M4 2.5V13.5L13 8L4 2.5Z" fill="#A78BFA" />
                      </svg>
                    )}
                  </button>

                  {/* Restart */}
                  <button
                    className="control-btn"
                    onClick={handleRestart}
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 8,
                      background: 'rgba(255, 255, 255, 0.06)',
                      border: '1px solid rgba(255, 255, 255, 0.12)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                    aria-label="重新播放"
                  >
                    <ReloadOutlined style={{ fontSize: 15, color: 'rgba(255, 255, 255, 0.7)' }} />
                  </button>

                  {/* Time Display */}
                  <div style={{
                    fontFamily: '"Fira Code", monospace',
                    fontSize: 12,
                    color: 'rgba(255, 255, 255, 0.6)',
                    letterSpacing: '0.04em',
                    marginLeft: 8,
                  }}>
                    <span style={{ color: '#A78BFA' }}>{formatTime(currentTime)}</span>
                    <span style={{ color: 'rgba(255, 255, 255, 0.25)', margin: '0 10px' }}>/</span>
                    <span>{formatTime(duration)}</span>
                  </div>
                </div>

                {/* Right Controls */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  {/* Fullscreen */}
                  <button
                    className="control-btn"
                    onClick={toggleFullscreen}
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 8,
                      background: 'rgba(255, 255, 255, 0.06)',
                      border: '1px solid rgba(255, 255, 255, 0.12)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                    aria-label={isFullscreen ? '退出全屏' : '全屏'}
                  >
                    {isFullscreen ? (
                      <CompressOutlined style={{ fontSize: 15, color: 'rgba(255, 255, 255, 0.7)' }} />
                    ) : (
                      <ExpandOutlined style={{ fontSize: 15, color: 'rgba(255, 255, 255, 0.7)' }} />
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Close Button */}
            <button
              onClick={() => setModalOpen(false)}
              style={{
                position: 'absolute',
                top: isFullscreen ? 24 : 16,
                right: isFullscreen ? 24 : 16,
                width: 36,
                height: 36,
                borderRadius: '50%',
                background: 'rgba(0, 0, 0, 0.5)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                opacity: showControls ? 1 : 0,
                pointerEvents: showControls ? 'auto' : 'none',
                zIndex: 10,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(225, 29, 72, 0.8)';
                e.currentTarget.style.borderColor = 'rgba(225, 29, 72, 0.8)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(0, 0, 0, 0.5)';
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.15)';
              }}
              aria-label="关闭"
            >
              <span style={{ fontSize: 20, color: '#fff', fontWeight: 300, lineHeight: 1 }}>×</span>
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default VideoPlayer;
