import React, { useEffect, useRef } from 'react';
import { BarChartOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';

const ExitReasonBarChart = ({ data }) => {
  const chartRef = useRef(null);

  const reasons = data?.total?.reasons || [];
  const totalCount = reasons.reduce((sum, item) => sum + (item.count || 0), 0);

  useEffect(() => {
    if (!chartRef.current) return;

    const chart = echarts.init(chartRef.current);

    const chartData = reasons.length > 0 ? reasons.map(item => ({
      name: item.name,
      value: item.count || 0
    })) : [];

    // 颜色方案 - 科技感多彩配色
    const colors = [
      { start: '#00f0ff', end: '#0080ff' },  // 青蓝
      { start: '#36d6ff', end: '#1890ff' },  // 天蓝
      { start: '#5b8def', end: '#7c4dff' },  // 紫蓝
      { start: '#ff6b9d', end: '#c850c0' },  // 粉紫
      { start: '#ffd700', end: '#ff9500' },  // 金橙
      { start: '#43e97b', end: '#38f9d7' },  // 翠绿
      { start: '#fa8231', end: '#f7ce68' },  // 橙黄
      { start: '#a18cd1', end: '#fbc2eb' },  // 淡紫
    ];

    const option = {
      backgroundColor: 'transparent',
      grid: {
        left: '3%',
        right: '3%',
        top: '25%',
        bottom: '8%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: chartData.map(item => item.name),
        axisLabel: {
          color: 'rgba(255, 255, 255, 0.8)',
          fontSize: 11,
          interval: 0,
          rotate: 0,
          margin: 8
        },
        axisLine: {
          lineStyle: { color: 'rgba(0, 240, 255, 0.2)' }
        },
        axisTick: { show: false },
        splitLine: { show: false }
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        axisLabel: {
          color: 'rgba(255, 255, 255, 0.5)',
          fontSize: 10
        },
        splitLine: {
          lineStyle: { color: 'rgba(0, 240, 255, 0.08)', type: 'dashed' }
        },
        axisLine: { show: false },
        axisTick: { show: false }
      },
      series: [
        // 主柱状图
        {
          type: 'bar',
          data: chartData.map((item, index) => ({
            value: item.value,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: colors[index % colors.length].start },
                { offset: 1, color: colors[index % colors.length].end }
              ]),
              borderRadius: [8, 8, 0, 0],
              shadowColor: colors[index % colors.length].start,
              shadowBlur: 10,
              shadowOffsetY: 5
            }
          })),
          barWidth: '50%',
          barGap: '30%',
          label: {
            show: true,
            position: 'top',
            distance: 8,
            color: '#00f0ff',
            fontSize: 14,
            fontWeight: 'bold',
            formatter: '{c}',
            textShadowColor: 'rgba(0, 240, 255, 0.8)',
            textShadowBlur: 10
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 20,
              shadowColor: 'rgba(0, 240, 255, 0.5)'
            }
          },
          animationDelay: (idx) => idx * 200,
          animationEasing: 'elasticOut',
          animationDuration: 1500
        },
        // 发光顶部效果
        {
          type: 'bar',
          data: chartData.map((item, index) => ({
            value: item.value,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(255, 255, 255, 0.8)' },
                { offset: 0.3, color: colors[index % colors.length].start },
                { offset: 1, color: 'transparent' }
              ]),
              borderRadius: [8, 8, 0, 0]
            }
          })),
          barWidth: '50%',
          barGap: '-100%',
          barCategoryGap: '30%',
          z: 2,
          silent: true,
          animationDelay: (idx) => idx * 200 + 300,
          animationEasing: 'cubicOut',
          animationDuration: 1800
        },
        // 背景柱状图
        {
          type: 'bar',
          data: chartData.map(() => Math.max(...chartData.map(d => d.value)) * 1.2),
          barWidth: '50%',
          barGap: '-100%',
          barCategoryGap: '30%',
          z: 0,
          silent: true,
          itemStyle: {
            color: 'rgba(0, 240, 255, 0.03)',
            borderRadius: [8, 8, 0, 0]
          },
          animation: false
        }
      ],
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(10, 15, 30, 0.95)',
        borderColor: 'rgba(0, 240, 255, 0.6)',
        borderWidth: 1.5,
        textStyle: { color: '#fff', fontSize: 12 },
        axisPointer: {
          type: 'shadow',
          shadowStyle: {
            color: 'rgba(0, 240, 255, 0.15)',
            shadowBlur: 10
          },
          lineStyle: {
            color: 'rgba(0, 240, 255, 0.3)',
            width: 2,
            type: 'dashed'
          }
        },
        padding: [10, 15],
        extraCssText: 'box-shadow: 0 0 20px rgba(0, 240, 255, 0.3); border-radius: 8px;',
        formatter: (params) => {
          const data = params[0];
          const color = colors[data.dataIndex % colors.length];
          return `
            <div style="font-weight: 600; margin-bottom: 4px;">${data.name}</div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${color.start}; box-shadow: 0 0 8px ${color.start};"></span>
              <span>数量: <strong style="color: ${color.start};">${data.value}</strong> 人</span>
            </div>
          `;
        }
      }
    };

    chart.setOption(option);

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [reasons]);

  return (
    <div className="exit-reason-bar-chart">
      <div className="chart-header">
        <div className="header-left">
          <div className="header-content">
            <BarChartOutlined />
            <span>出监类型统计</span>
          </div>
          <div className="header-line"></div>
        </div>
        <div className="header-total">
          <span className="total-label">总出监</span>
          <span className="total-value">{totalCount}</span>
          <span className="total-unit">人</span>
        </div>
        <div className="header-decor">
          <span className="decor-dot"></span>
          <span className="decor-dot"></span>
          <span className="decor-dot"></span>
        </div>
      </div>
      <div className="chart-content">
        <div ref={chartRef} className="echarts-container" />
      </div>
    </div>
  );
};

export default ExitReasonBarChart;