import React, { useState } from 'react';
import { Modal, Spin } from 'antd';
import { VideoCameraOutlined } from '@ant-design/icons';
import { video as videoApi } from '@/api/globApi';

const VideoPlayer = ({ startTime, endTime, cameraIndex = 0 }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [streamUrl, setStreamUrl] = useState(null);

  const handlePlay = async () => {
    if (!startTime || !endTime) {
      return;
    }
    setLoading(true);
    try {
      const res = await videoApi.getStreamUrl({
        start_time: startTime,
        end_time: endTime,
        camera: cameraIndex,
      });
      if (res?.url) {
        setStreamUrl(res.url);
        setModalOpen(true);
      }
    } catch (error) {
      console.error('获取视频流失败', error);
    } finally {
      setLoading(false);
    }
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
        onCancel={() => {
          setModalOpen(false);
          setStreamUrl(null);
        }}
        footer={null}
        width={800}
        centered
      >
        {streamUrl && (
          <video
            src={streamUrl}
            controls
            autoPlay
            style={{ width: '100%', maxHeight: '70vh' }}
          />
        )}
      </Modal>
    </>
  );
};

export default VideoPlayer;