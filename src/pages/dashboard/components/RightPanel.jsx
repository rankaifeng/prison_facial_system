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
  const scrollIntervalRef = useRef(null);

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

    const shouldScroll = container.scrollHeight > container.clientHeight;
    setIsScrolling(shouldScroll && messages.length > 0);
  }, [messages]);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container) return;

    if (isScrolling) {
      const scrollStep = 1;
      const delay = 50;

      scrollIntervalRef.current = setInterval(() => {
        if (container.scrollTop >= container.scrollHeight - container.clientHeight) {
          container.scrollTop = 0;
        } else {
          container.scrollTop += scrollStep;
        }
      }, delay);
    } else {
      if (scrollIntervalRef.current) {
        clearInterval(scrollIntervalRef.current);
        scrollIntervalRef.current = null;
      }
    }

    return () => {
      if (scrollIntervalRef.current) {
        clearInterval(scrollIntervalRef.current);
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
            messages.map((msg, index) => (
              <div key={`${msg.id || index}`} className="message-item">
                <div className="message-content">
                  <div className="message-text">
                    <div className="person-name">{msg.prisoner_name}在<span style={{ color: 'red', margin: '0 5px' }}>{msg.exit_date}</span></div>
                    <div className="action-text">{msg.reason}</div>
                    {msg.hospital_name && <div style={{ color: '#00f0ff', marginLeft: 5 }}>-{msg.hospital_name}</div>}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
         <div className="message-scroll">
          {messages.length === 0 ? (
            renderEmptyState()
          ) : (
            messages.map((msg, index) => (
              <div key={`${msg.id || index}`} className="message-item">
                <div className="message-content">
                  <div className="message-text">
                    <div className="person-name">{msg.prisoner_name}在<span style={{ color: 'red', margin: '0 5px' }}>{msg.exit_date}</span></div>
                    <div className="action-text">{msg.reason}</div>
                    {msg.hospital_name && <div style={{ color: '#00f0ff', marginLeft: 5 }}>-{msg.hospital_name}</div>}
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