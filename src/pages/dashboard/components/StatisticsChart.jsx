import React from 'react';
import { AlertOutlined } from '@ant-design/icons';

const StatisticsChart = ({ data }) => {
  const exitCount = data?.total?.exit_count || 0;
  const reasons = data?.total?.reasons || [];

  const colors = ['#00f0ff', '#3b7dd8', '#52c41a', '#faad14', '#722ed1'];

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
        <div className="exit-hero">
          <div className="exit-hero-label">今日出监人数</div>
          <span className="exit-hero-number">{exitCount}</span>
          <span className="exit-hero-unit">人</span>
        </div>
        <div className="exit-reason-list">
          {reasons.map((r, i) => (
            <div key={i} className="exit-reason-row">
              <span className="reason-dot" style={{ background: colors[i % colors.length] }} />
              <span className="reason-name">{r.name}</span>
              <span className="reason-bar-wrap">
                <span
                  className="reason-bar"
                  style={{
                    width: `${exitCount > 0 ? (r.count / exitCount) * 100 : 0}%`,
                    background: colors[i % colors.length],
                  }}
                />
              </span>
              <span className="reason-count">{r.count || 0}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StatisticsChart;
