import React from 'react';
import { BellOutlined, RightOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { useNavigate } from 'react-router-dom';

const RightPanel = ({ messages }) => {
  const navigate = useNavigate();

  const duplicatedMessages = [...messages, ...messages];

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
      <div className="message-list">
        <div className="message-scroll">
          {duplicatedMessages.map((msg, index) => (
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
    </div>
  );
};

export default RightPanel;