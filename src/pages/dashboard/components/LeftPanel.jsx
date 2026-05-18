import React from 'react';
import { UserOutlined, HeartOutlined, MedicineBoxOutlined, LockOutlined, DisconnectOutlined, HomeOutlined, ThunderboltOutlined, ArrowUpOutlined } from '@ant-design/icons';

const LeftPanel = ({ realtimeData }) => {
  // 实时在监总人数 - 来自API的 total.in_prison_count
  const total = realtimeData?.total?.in_prison_count || 0;

  // 各出监原因数量 - 来自API的 total.reasons，动态渲染
  const reasons = realtimeData?.total?.reasons || [];

  return (
    <div className="left-panel">
      <div className="panel-section total-section">
        <div className="chart-header">
          <div className="header-content">
            <UserOutlined />
            <span>实时在监总人数</span>
          </div>
          <div className="header-line"></div>
          <div className="header-decor">
            <span className="decor-dot"></span>
            <span className="decor-dot"></span>
            <span className="decor-dot"></span>
          </div>
        </div>
        <div className="total-display">
          <div className="total-circle" style={{ marginTop: 20 }}>
            <div className="total-value">{222}</div>
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
          <div className="header-content">
            <LockOutlined />
            <span>监狱罪犯情况</span>
          </div>
          <div className="header-line"></div>
          <div className="header-decor">
            <span className="decor-dot"></span>
            <span className="decor-dot"></span>
            <span className="decor-dot"></span>
          </div>
          <div className="header-stat">
            <span>当天出监总人数：{realtimeData?.total?.exit_count || 0}</span>
          </div>
        </div>
        <div className="stats-grid">
          {reasons.map((reason, index) => {
            const icons = [UserOutlined, ThunderboltOutlined, MedicineBoxOutlined, LockOutlined, DisconnectOutlined];
            const iconClass = ['in-prison', 'working', 'hospital', 'isolated', 'quarantine'];
            const IconComponent = icons[index % icons.length];
            return (
              <div key={reason.name} className="stat-box">
                <div className={`stat-icon ${iconClass[index % iconClass.length]}`}>
                  <IconComponent />
                </div>
                <div className="stat-content">
                  <div className="stat-label">{reason.name}</div>
                  <div className="stat-number">{reason.count}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default LeftPanel;