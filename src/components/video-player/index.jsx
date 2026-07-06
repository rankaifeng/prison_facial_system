import React, { useState, useRef } from 'react';
import { Modal } from 'antd';
import { VideoCameraOutlined } from '@ant-design/icons';

const VideoPlayer = ({ itemData }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const videoRef = useRef(null);

  if (!itemData?.video_url) {
    return (
      <div style={{ textAlign: 'center', color: '#999' }}>
        <VideoCameraOutlined style={{ fontSize: 16 }} />
        <div style={{ fontSize: 12 }}>暂无录像</div>
      </div>
    );
  }

  return (
    <>
      <div
        onClick={() => setModalOpen(true)}
        style={{ cursor: 'pointer', textAlign: 'center', color: '#1890ff' }}
      >
        <VideoCameraOutlined style={{ fontSize: 16 }} />
        <div style={{ fontSize: 12 }}>播放</div>
      </div>

      <Modal
        title="视频播放"
        open={modalOpen}
        onCancel={() => {
          if (videoRef.current) {
            videoRef.current.pause();
          }
          setModalOpen(false);
        }}
        footer={null}
        width={800}
        destroyOnClose
      >
        <video
          ref={videoRef}
          src={itemData.video_url}
          controls
          autoPlay
          style={{ width: '100%', display: 'block' }}
        />
      </Modal>
    </>
  );
};

export default VideoPlayer;
