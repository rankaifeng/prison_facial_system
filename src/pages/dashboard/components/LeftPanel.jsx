import React from 'react';
import { UserOutlined, HeartOutlined, MedicineBoxOutlined, LockOutlined, DisconnectOutlined, HomeOutlined, ThunderboltOutlined } from '@ant-design/icons';

const LeftPanel = ({ realtimeData, prisonStats }) => {
  return (
    <div className="left-panel">
      <div className="panel-section total-section">
        <div className="section-header">
          <UserOutlined />
          <span>实时在监总人数</span>
        </div>
        <div className="total-number">{realtimeData?.total || 0}</div>
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
              <div className="stat-label">在监</div>
              <div className="stat-number">{prisonStats?.inPrison || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon working">
              <ThunderboltOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">出工</div>
              <div className="stat-number">{prisonStats?.working || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon hospital">
              <MedicineBoxOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">住院</div>
              <div className="stat-number">{prisonStats?.hospital || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon isolated">
              <LockOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">禁闭</div>
              <div className="stat-number">{prisonStats?.isolated || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon quarantine">
              <DisconnectOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">隔离</div>
              <div className="stat-number">{prisonStats?.quarantine || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon visiting">
              <HomeOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">探亲</div>
              <div className="stat-number">{prisonStats?.visiting || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon punishment">
              <HeartOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">惩戒</div>
              <div className="stat-number">{prisonStats?.punishment || 0}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeftPanel;