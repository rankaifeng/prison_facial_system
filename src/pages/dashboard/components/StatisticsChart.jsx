import React, { useEffect, useRef, useState } from 'react';
import { PieChartOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';

const StatisticsChart = ({ data }) => {
  const chartRef = useRef(null);

  // workStatistics API 返回的数据结构: data.total.exit_count, data.total.entry_count
  const exitCount = data?.total?.exit_count || 0;

  useEffect(() => {
    if (!chartRef.current) return;

    const chart = echarts.init(chartRef.current);

    const defaultValue = 0;
    const totalValue = exitCount || defaultValue;
    const maxValue = 500;

    const option = {
      backgroundColor: 'transparent',
      series: [
        {
          type: 'gauge',
          startAngle: 90,
          endAngle: -270,
          radius: '90%',
          center: ['50%', '55%'],
          pointer: {
            show: false,
          },
          progress: {
            show: true,
            overlap: false,
            roundCap: true,
            clip: false,
            itemStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 1,
                y2: 0,
                colorStops: [
                  { offset: 0, color: '#00f0ff' },
                  { offset: 0.5, color: '#1877ff' },
                  { offset: 1, color: '#00f0ff' },
                ],
              },
            },
          },
          axisLine: {
            lineStyle: {
              width: 18,
              color: [[1, 'rgba(0, 240, 255, 0.15)']],
            },
          },
          splitLine: {
            show: false,
          },
          axisTick: {
            show: false,
          },
          axisLabel: {
            show: false,
          },
          data: [
            {
              value: totalValue,
              name: '出监人数',
              title: {
                offsetCenter: ['0%', '30%'],
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: 12,
              },
              detail: {
                offsetCenter: ['0%', '0%'],
                color: '#00f0ff',
                fontSize: 36,
                fontWeight: 'bold',
                formatter: function(value) {
                  return Math.round(value);
                },
              },
              itemStyle: {
                color: '#00f0ff',
              },
            },
          ],
          title: {
            fontSize: 12,
            color: 'rgba(255, 255, 255, 0.7)',
          },
          detail: {
            fontSize: 36,
            fontWeight: 'bold',
            color: '#00f0ff',
            formatter: '{value}',
          },
        },
        {
          type: 'pie',
          radius: ['58%', '62%'],
          center: ['50%', '55%'],
          avoidLabelOverlap: false,
          label: {
            show: false,
          },
          labelLine: {
            show: false,
          },
          data: [],
        },
      ],
    };

    chart.setOption(option);

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [exitCount]);

  return (
    <div className="statistics-chart">
      <div className="chart-header">
        <div className="header-content">
          <PieChartOutlined />
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
        <div className="chart-area">
          <div ref={chartRef} className="echarts-container" />
        </div>
      </div>
    </div>
  );
};

export default StatisticsChart;