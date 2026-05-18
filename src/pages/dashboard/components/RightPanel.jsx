import React, { useEffect, useState } from 'react';
import { BellOutlined, RightOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import { prisonMessages } from '@/api/globApi';

const RightPanel = () => {
  const [messages, setMessages] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchMessages();
  }, []);

  const fetchMessages = async () => {
    try {
      const res = await prisonMessages.list({ page: 1, limit: 50 });
      setMessages(res);
    } catch (error) {
      console.error('获取监狱消息失败:', error);
    }
  };

  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    const date = new Date(timeStr);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    return timeStr.split(' ')[0];
  };

  const getActionText = (reason) => {
    const actionMap = {
      '刑满释放': '刑满释放出监',
      '外出就医': '外出就医出监',
      '外出教育': '外出教育出监',
      '离监探亲': '离监探亲出监',
      '押回重审': '押回重审出监',
    };
    return actionMap[reason] || '出监';
  };

  const duplicatedMessages = [...messages, ...messages];
  const shouldScroll = messages.length > 3;
  console.log("duplicatedMessages", duplicatedMessages);

  const renderEmptyState = () => (
    <div className="message-empty">
      <BellOutlined className="empty-icon" />
      <span className="empty-text">暂无消息</span>
    </div>
  );

  return (
    <div className="right-panel">
      <div className="panel-header">
        <div className="header-left">
          <BellOutlined />
          <span>监狱消息</span>
        </div>
        <div className="header-line"></div>
        <div className="header-decor">
          <span className="decor-dot"></span>
          <span className="decor-dot"></span>
          <span className="decor-dot"></span>
        </div>
        <Button
          type="link"
          size="small"
          className="detail-btn"
          onClick={() => navigate('/statistics')}
        >
          详情 <RightOutlined />
        </Button>
      </div>
      <div className="message-list" style={{ overflow: shouldScroll ? 'hidden' : 'auto' }}>
        <div
          className="message-scroll"
          style={{ animationPlayState: shouldScroll ? 'running' : 'paused' }}
        >
          {duplicatedMessages.length === 0 ? (
            renderEmptyState()
          ) : (
            duplicatedMessages.map((msg, index) => (
              <div key={`${msg.id || index}-${index >= messages.length ? 'dup' : 'orig'}`} className="message-item">
                <div className="message-content">
                  <div className="message-text">
                    <span className="prison-tag">【{msg.prison_area_name || '未知监区'}】</span>
                    <span className="person-name">{msg.prisoner_name}</span>
                    <span className="action-text">{getActionText(msg.reason)}</span>
                    <span className="time-text">{formatTime(msg.created_at)}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default RightPanel;