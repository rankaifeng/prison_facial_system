import React from 'react';
import { UserOutlined, HeartOutlined, MedicineBoxOutlined, LockOutlined, DisconnectOutlined, HomeOutlined, ThunderboltOutlined } from '@ant-design/icons';

const LeftPanel = ({ realtimeData, prisonStats }) => {
  const total = realtimeData?.total || 890;

  return (
    <div className="left-panel">
      <div className="panel-section total-section">
        <div className="chart-header">
          <UserOutlined />
          <span>实时在监总人数</span>
        </div>
        <div className="total-display">
          <div className="total-circle">
            <div className="total-value">{total}</div>
            <div className="total-unit">人</div>
          </div>
          <div className="total-decoration">
            <div className="decoration-line"></div>
            <div className="decoration-dot"></div>
          </div>
        </div>
      </div>

      <div className="panel-section stats-section">
        <div className="section-header">
          <span>监狱罪犯情况</span>
        </div>
        <div className="stats-grid">
          <div className="stat-box">
            <div className="stat-icon in-prison">
              <UserOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">刑满释放</div>
              <div className="stat-number">{prisonStats?.inPrison || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon working">
              <ThunderboltOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">外出就医</div>
              <div className="stat-number">{prisonStats?.working || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon hospital">
              <MedicineBoxOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">外出教育</div>
              <div className="stat-number">{prisonStats?.hospital || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon isolated">
              <LockOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">离监探亲</div>
              <div className="stat-number">{prisonStats?.isolated || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon quarantine">
              <DisconnectOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">押回重审</div>
              <div className="stat-number">{prisonStats?.quarantine || 0}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeftPanel;