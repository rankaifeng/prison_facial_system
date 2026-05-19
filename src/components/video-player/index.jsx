import React, { useState } from 'react';
import { Modal } from 'antd';
import { VideoCameraOutlined } from '@ant-design/icons';

const VideoPlayer = ({ src }) => {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <div
        onClick={() => setModalOpen(true)}
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
        <VideoCameraOutlined style={{ fontSize: 16, color: '#00f0ff' }} />
      </div>
      <Modal
        title="录像播放"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={800}
        centered
      >
        <video
          src='https://www.w3schools.com/html/mov_bbb.mp4'
          controls
          autoPlay
          style={{ width: '100%', maxHeight: '70vh' }}
        />
      </Modal>
    </>
  );
};

export default VideoPlayer;