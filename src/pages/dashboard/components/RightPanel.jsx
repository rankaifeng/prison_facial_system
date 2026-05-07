import React, { useEffect, useRef } from 'react';
import { BellOutlined, RightOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import './index.less';

const RightPanel = ({ messages }) => {
  const navigate = useNavigate();
  const scrollRef = useRef(null);

  return (
    <div className="right-panel">
      <div className="panel-header">
        <BellOutlined />
        <span>监狱消息</span>
      </div>
      <div className="message-list" ref={scrollRef}>
        {messages?.map((msg, index) => (
          <div key={msg.id || index} className="message-item">
            <div className="message-content">
              <div className="message-text">
                <span className="prison-tag">{msg.prisonName}</span>
                <span className="person-name">{msg.personName}</span>
                <span className="action-text">{msg.action}</span>
                <span className="time-text">{msg.time}</span>
              </div>
              {msg.detail && (
                <Button
                  type="link"
                  size="small"
                  className="detail-btn"
                  onClick={() => navigate('/statistics')}
                >
                  详情 <RightOutlined />
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RightPanel;
