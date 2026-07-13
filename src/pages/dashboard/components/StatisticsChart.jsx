import React from 'react';
import { AlertOutlined } from '@ant-design/icons';

const StatisticsChart = ({ data }) => {
  const exitCount = data?.total?.exit_count || 0;
  const reasons = data?.total?.reasons || [];

  return (
    <div className="statistics-chart">
      <div className="chart-header">
        <div className="header-content">
          <AlertOutlined />
          <span>当日出监人数统计</span>
        </div>
        <div className="header-line"></div>
        <div className="header-decor">
          <span className="decor-dot"></span>
          <span className="decor-dot"></span>
          <span className="decor-dot"></span>
        </div>
      </div>
      <div className="chart-content">
        <div className="exit-count-display">
          <div className="exit-count-ring">
            <div className="exit-count-number">{exitCount}</div>
            <div className="exit-count-label">今日出监</div>
          </div>
          <div className="exit-count-ring-glow"></div>
        </div>
        <div className="exit-reason-tags">
          {reasons.filter(r => r.count > 0).map((r, i) => (
            <div key={i} className="exit-reason-tag">
              <span className="tag-name">{r.name}</span>
              <span className="tag-count">{r.count}</span>
            </div>
          ))}
          {reasons.every(r => r.count === 0) && (
            <div className="exit-reason-empty">暂无出监记录</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatisticsChart;
