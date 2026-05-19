import React, { useEffect, useState, useRef } from 'react';
import { BellOutlined, RightOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import { prisonMessages } from '@/api/globApi';

const RightPanel = ({ onDataUpdate }) => {
  const [messages, setMessages] = useState([]);
  const [shouldScroll, setShouldScroll] = useState(false);
  const navigate = useNavigate();
  const scrollRef = useRef(null);

  useEffect(() => {
    fetchMessages();
  }, []);

  useEffect(() => {
    if (onDataUpdate) {
      onDataUpdate(fetchMessages);
    }
  }, [onDataUpdate]);

  const fetchMessages = async () => {
    try {
      const res = await prisonMessages.list({ page: 1, limit: 60 });
      const data = Array.isArray(res) ? res : (res?.data || []);
      setMessages(data);
    } catch (error) {
      console.error('获取监狱消息失败:', error);
    }
  };



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
      <div
        className="message-list"
        style={{ overflow: shouldScroll ? 'hidden' : 'visible' }}
        ref={scrollRef}
      >
        <div
          className="message-scroll"
          style={{ animationPlayState: shouldScroll ? 'running' : 'paused' }}
        >
          {messages.length === 0 ? (
            renderEmptyState()
          ) : (
            messages.map((msg, index) => (
              <div key={`${msg.id || index}-${index >= messages.length ? 'dup' : 'orig'}`} className="message-item">
                <div className="message-content">
                  <div className="message-text">
                    <span className="prison-tag">【{msg.prison_area_name || '未知监区'}】</span>
                    <span className="person-name">{msg.prisoner_name}在<span style={{ color: 'red', margin: '0 5px' }}>{msg.exit_date}</span></span>
                    <span className="action-text">{msg.reason}</span>
                    {msg.hospital_name && <span style={{ color: '#00f0ff', marginLeft: 5 }}>-{msg.hospital_name}</span>}
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