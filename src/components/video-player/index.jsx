import React, { useState, useRef, useEffect } from 'react';
import { Modal, Spin, message } from 'antd';
import { VideoCameraOutlined, ReloadOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { video as videoApi } from '@/api/globApi';

const VideoPlayer = ({ itemData }) => {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <div
        onClick={() => {
          if (!itemData?.video_url) {
            message.warning('暂无录像文件');
            return;
          }
          setModalOpen(true);
        }}
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
        <VideoCameraOutlined style={{ fontSize: 16, color: '#00f0ff' }} />
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
        onCancel={() => setModalOpen(false)}
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
          <video src={itemData?.video_url} controls autoPlay style={{ width: '100%', height: '100%', objectFit: 'contain' }}
          />
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