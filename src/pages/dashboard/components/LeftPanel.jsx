import React from 'react';
import { UserOutlined, HeartOutlined, MedicineBoxOutlined, LockOutlined, DisconnectOutlined, HomeOutlined, ThunderboltOutlined, ArrowUpOutlined } from '@ant-design/icons';
import StatisticsChart from './StatisticsChart';

const LeftPanel = ({ data }) => {
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
        <StatisticsChart data={data} />
      </div>
    </div>
  );
};

export default LeftPanel;