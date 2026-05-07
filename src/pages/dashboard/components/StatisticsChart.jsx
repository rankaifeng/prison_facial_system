import React from 'react';
import { LineChartOutlined } from '@ant-design/icons';
import './index.less';

const StatisticsChart = ({ data }) => {
  const months = data?.map(item => item.month) || ['1月', '2月', '3月', '4月', '5月', '6月'];
  const prisons = data?.prisons || [];

  const colors = ['#1890ff', '#52c41a', '#ff4d4f', '#faad14', '#722ed1', '#00cec8', '#ff8a00'];

  return (
    <div className="statistics-chart">
      <div className="chart-header">
        <LineChartOutlined />
        <span>出工统计</span>
      </div>
      <div className="chart-content">
        <div className="chart-legend">
          {prisons.map((prison, index) => (
            <div key={prison.name} className="legend-item">
              <span className="legend-color" style={{ background: colors[index % colors.length] }}></span>
              <span className="legend-name">{prison.name}</span>
            </div>
          ))}
        </div>
        <div className="chart-area">
          {prisons.length > 0 ? (
            <div className="chart-lines">
              {prisons.map((prison, pIndex) => (
                <div
                  key={prison.name}
                  className="chart-line"
                  style={{ '--line-color': colors[pIndex % colors.length] }}
                >
                  {prison.values?.map((value, vIndex) => (
                    <div key={vIndex} className="line-point">
                      <div
                        className="point-dot"
                        style={{ height: `${value * 10}%` }}
                      >
                        <span className="point-value">{value}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ))}
              <div className="chart-x-axis">
                {months.map((month, index) => (
                  <span key={index} className="x-label">{month}</span>
                ))}
              </div>
            </div>
          ) : (
            <div className="chart-placeholder">
              <LineChartOutlined />
              <span>暂无数据</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatisticsChart;
