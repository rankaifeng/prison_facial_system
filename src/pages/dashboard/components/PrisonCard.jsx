import React from 'react';
import { TeamOutlined } from '@ant-design/icons';

const PrisonCard = ({ name, totalCount, workCount, imageUrl }) => {
  return (
    <div className="prison-card">
      <div className="prison-image">
        <img src={imageUrl || '/imgs/jy.png'} alt={name} />
        <div className="prison-overlay">
          <div className="prison-stats">
            <div className="stat-item">
              <TeamOutlined />
              <span className="stat-label">总人数</span>
              <span className="stat-value">{totalCount || 0}</span>
            </div>
            <div className="stat-item highlight">
              <TeamOutlined />
              <span className="stat-label">出工</span>
              <span className="stat-value">{workCount || 0}</span>
            </div>
          </div>
        </div>
      </div>
      <div className="prison-name">{name}</div>
    </div>
  );
};

export default PrisonCard;