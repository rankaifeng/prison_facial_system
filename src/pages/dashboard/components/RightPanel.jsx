import React, { useEffect, useState, useRef } from 'react';
import { BellOutlined, RightOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import { prisonMessages } from '@/api/globApi';
import './RightPanel.less';

const RightPanel = ({ onDataUpdate }) => {
  const [messages, setMessages] = useState([]);
  const navigate = useNavigate();
  const scrollRef = useRef(null);
  const animRef = useRef(null);

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

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || messages.length <= 3) {
      if (animRef.current) {
        cancelAnimationFrame(animRef.current);
      }
      return;
    }

    const maxScroll = el.scrollHeight - el.clientHeight;
    if (maxScroll <= 0) return;

    let scrollTop = 0;
    const speed = 40;

    const animate = () => {
      scrollTop += speed / 60;
      if (scrollTop >= maxScroll) {
        scrollTop = 0;
      }
      el.scrollTop = scrollTop;
      animRef.current = requestAnimationFrame(animate);
    };

    animRef.current = requestAnimationFrame(animate);

    return () => {
      if (animRef.current) {
        cancelAnimationFrame(animRef.current);
      }
    };
  }, [messages.length]);

  const renderEmptyState = () => (
    <div className="message-empty">
      <BellOutlined className="empty-icon" />
      <span className="empty-text">暂无消息</span>
    </div>
  );

  const renderMessages = () => (
    messages.map((msg, index) => (
      <div key={msg.id || index} className="message-item">
        <div className="message-dot" />
        <div className="message-text">
          <span className="person-name">{msg.prisoner_name}</span>
          <span className="date">{msg.exit_date}</span>
          <span className="reason">{msg.reason}</span>
          {msg.hospital_name && <span className="hospital">{msg.hospital_name}</span>}
        </div>
      </div>
    ))
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
      <div className="message-list" ref={scrollRef}>
        <div className="message-scroll">
          {messages.length === 0 ? renderEmptyState() : renderMessages()}
        </div>
      </div>
    </div>
  );
};

export default RightPanel;