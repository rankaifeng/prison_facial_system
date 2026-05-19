import React, { useEffect, useState, useRef } from 'react';
import { BellOutlined, RightOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import { prisonMessages } from '@/api/globApi';

const RightPanel = ({ onDataUpdate }) => {
  const [messages, setMessages] = useState([]);
  const [isScrolling, setIsScrolling] = useState(false);
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

  useEffect(() => {
    const container = scrollRef.current;
    if (!container) return;

    // 内容超过容器高度且消息多于1条时滚动
    const shouldScroll = messages.length > 3;
    setIsScrolling(shouldScroll);
  }, [messages]);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container || !isScrolling) return;

    let animationId;
    let scrollTop = 0;
    const speed = 0.3;
    // 由于内容被复制了两份，滚动到一半就是一组内容的长度
    const maxScroll = container.scrollHeight / 2;

    const scroll = () => {
      scrollTop += speed;
      if (scrollTop >= maxScroll) {
        scrollTop = 0;
      }
      container.scrollTop = scrollTop;
      animationId = requestAnimationFrame(scroll);
    };

    animationId = requestAnimationFrame(scroll);

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [isScrolling]);

  const fetchMessages = async () => {
    try {
      const res = await prisonMessages.list({ page: 1, limit: 60 });
      const data = Array.isArray(res) ? res : (res?.data || []);
      //只取data的前五条
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
        ref={scrollRef}
      >
        <div className="message-scroll">
          {messages.length === 0 ? (
            renderEmptyState()
          ) : (
            <>
              {messages.map((msg, index) => (
                <div key={`orig-${msg.id || index}`} className="message-item">
                  <div className="message-content">
                    <div className="message-text">
                      <div className="person-name">{msg.prisoner_name}在<span style={{ color: 'red', margin: '0 5px' }}>{msg.exit_date}</span></div>
                      <div className="action-text">{msg.reason}</div>
                      {msg.hospital_name && <div style={{ color: '#00f0ff', marginLeft: 5 }}>-{msg.hospital_name}</div>}
                    </div>
                  </div>
                </div>
              ))}
              {messages.map((msg, index) => (
                <div key={`dup-${msg.id || index}`} className="message-item">
                  <div className="message-content">
                    <div className="message-text">
                      <div className="person-name">{msg.prisoner_name}在<span style={{ color: 'red', margin: '0 5px' }}>{msg.exit_date}</span></div>
                      <div className="action-text">{msg.reason}</div>
                      {msg.hospital_name && <div style={{ color: '#00f0ff', marginLeft: 5 }}>-{msg.hospital_name}</div>}
                    </div>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default RightPanel;