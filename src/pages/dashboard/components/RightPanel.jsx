import React, { useEffect, useRef } from 'react';
import { BellOutlined, RightOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { useNavigate } from 'react-router-dom';

const RightPanel = ({ messages }) => {
  const navigate = useNavigate();
  const scrollRef = useRef(null);

  useEffect(() => {
    const scrollContainer = scrollRef.current;
    if (!scrollContainer) return;

    let animationId;
    let scrollTop = 0;

    const scroll = () => {
      scrollTop += 1;
      if (scrollTop >= scrollContainer.scrollHeight / 2) {
        scrollTop = 0;
      }
      scrollContainer.scrollTop = scrollTop;
      animationId = requestAnimationFrame(scroll);
    };

    const timeoutId = setTimeout(() => {
      animationId = requestAnimationFrame(scroll);
    }, 2000);

    return () => {
      clearTimeout(timeoutId);
      cancelAnimationFrame(animationId);
    };
  }, []);

  return (
    <div className="right-panel">
      <div className="panel-header">
        <div className="header-left">
          <BellOutlined />
          <span>监狱消息</span>
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
        {[...messages, ...messages].map((msg, index) => (
          <div key={`${msg.id || index}-${index >= messages.length ? 'dup' : 'orig'}`} className="message-item">
            <div className="message-content">
              <div className="message-text">
                <span className="prison-tag">{msg.prisonName}</span>
                <span className="person-name">{msg.personName}</span>
                <span className="action-text">{msg.action}</span>
                <span className="time-text">{msg.time}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RightPanel;