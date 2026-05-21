import React, { useState } from 'react';
import { Modal, Image, Button, Tabs, Tag } from 'antd';
import { DownloadOutlined, PictureOutlined, VideoCameraOutlined, FileOutlined, PlayCircleOutlined } from '@ant-design/icons';

const AttachmentPreviewModal = ({ visible, attachments = [], onClose }) => {
  const [previewVisible, setPreviewVisible] = useState(false);
  const [currentVideo, setCurrentVideo] = useState(null);

  const isImage = (url) => {
    const ext = url?.split('.').pop()?.toLowerCase();
    return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(ext);
  };

  const isVideo = (url) => {
    const ext = url?.split('.').pop()?.toLowerCase();
    return ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'].includes(ext);
  };

  const handleDownload = (url) => {
    const a = document.createElement('a');
    a.href = url;
    a.download = url.split('/').pop();
    a.target = '_blank';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const images = attachments.filter(isImage);
  const videos = attachments.filter(isVideo);
  const files = attachments.filter(url => !isImage(url) && !isVideo(url));

  const tabItems = [
    {
      key: 'images',
      label: (
        <span>
          <PictureOutlined /> 图片 ({images.length})
        </span>
      ),
      children: (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
          {images.map((url, index) => (
            <Image
              src={url}
              style={{ width: 180, height: 140}}
            />
          ))}
          {images.length === 0 && <div style={{ color: '#666' }}>暂无图片附件</div>}
        </div>
      ),
    },
    {
      key: 'videos',
      label: (
        <span>
          <VideoCameraOutlined /> 视频 ({videos.length})
        </span>
      ),
      children: (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
          {videos.map((url, index) => (
            <div
              key={index}
              style={{
                width: 180,
                height: 140,
                borderRadius: 8,
                overflow: 'hidden',
                border: '1px solid #333',
                position: 'relative',
                cursor: 'pointer',
                background: '#000',
              }}
              onClick={() => {
                setCurrentVideo(url);
                setPreviewVisible(true);
              }}
            >
              <div style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <PlayCircleOutlined style={{ fontSize: 48, color: '#00f0ff' }} />
              </div>
              <div style={{
                position: 'absolute',
                bottom: 8,
                right: 8,
                background: 'rgba(0,0,0,0.6)',
                borderRadius: 4,
                padding: '4px 8px',
              }}>
                <VideoCameraOutlined style={{ color: '#fff' }} />
              </div>
            </div>
          ))}
          {videos.length === 0 && <div style={{ color: '#666' }}>暂无视频附件</div>}
        </div>
      ),
    },
    {
      key: 'files',
      label: (
        <span>
          <FileOutlined /> 文件 ({files.length})
        </span>
      ),
      children: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {files.map((url, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                background: '#1a1a2e',
                borderRadius: 8,
                border: '1px solid #333',
              }}
            >
              <span style={{ color: '#fff' }}>{url.split('/').pop()}</span>
              <Button
                type="primary"
                size="small"
                icon={<DownloadOutlined />}
                onClick={() => handleDownload(url)}
              >
                下载
              </Button>
            </div>
          ))}
          {files.length === 0 && <div style={{ color: '#666' }}>暂无其他文件</div>}
        </div>
      ),
    },
  ];

  return (
    <>
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>附件预览</span>
            <Tag color="blue">{attachments.length} 个附件</Tag>
          </div>
        }
        open={visible}
        onCancel={onClose}
        footer={null}
        width={700}
        bodyStyle={{ padding: '16px 0' }}
      >
        <Tabs items={tabItems} defaultActiveKey="images" />
      </Modal>

      <Modal
        title="视频播放"
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width={800}
      >
        <video
          src={currentVideo}
          controls
          style={{ width: '100%', maxHeight: '60vh' }}
          autoPlay
        />
      </Modal>
    </>
  );
};

export default AttachmentPreviewModal;