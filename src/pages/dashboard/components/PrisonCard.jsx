import React from 'react';
import { EnvironmentOutlined, TeamOutlined } from '@ant-design/icons';
import './index.less';

const PrisonCard = ({ name, totalCount, workCount, imageUrl }) => {
  return (
    <div className="prison-card">
      <div className="prison-image">
        {imageUrl ? (
          <img src={imageUrl} alt={name} />
        ) : (
          <div className="prison-placeholder">
            <EnvironmentOutlined />
            <span>监狱</span>
          </div>
        )}
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
