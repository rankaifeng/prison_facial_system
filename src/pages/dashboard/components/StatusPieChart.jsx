import React, { useEffect, useRef } from 'react';
import { PieChartOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';

const StatusPieChart = ({ data }) => {
  const chartRef = useRef(null);

  const reasons = data?.total?.reasons || [];
  const totalCount = (data?.total?.exit_count) || reasons.reduce((s, r) => s + (r.count || 0), 0);

  useEffect(() => {
    if (!chartRef.current) return;

    const chart = echarts.init(chartRef.current);

    const defaultData = [
      { name: '刑满释放', value: 0 },
      { name: '外出就医', value: 0 },
      { name: '外出教育', value: 0 },
      { name: '离监探亲', value: 0 },
      { name: '押回重审', value: 0 }
    ];

    const chartData = reasons.length > 0 ? reasons.map(item => ({
      name: item.name,
      value: item.count || 0
    })) : defaultData;

    const colorList = [
      new echarts.graphic.LinearGradient(0, 0, 1, 1, [
        { offset: 0, color: '#00f0ff' },
        { offset: 1, color: '#0080ff' }
      ]),
      new echarts.graphic.LinearGradient(0, 0, 1, 1, [
        { offset: 0, color: '#52c41a' },
        { offset: 1, color: '#237804' }
      ]),
      new echarts.graphic.LinearGradient(0, 0, 1, 1, [
        { offset: 0, color: '#ff7a45' },
        { offset: 1, color: '#cf1322' }
      ]),
      new echarts.graphic.LinearGradient(0, 0, 1, 1, [
        { offset: 0, color: '#ffc53d' },
        { offset: 1, color: '#d48806' }
      ]),
      new echarts.graphic.LinearGradient(0, 0, 1, 1, [
        { offset: 0, color: '#b37feb' },
        { offset: 1, color: '#531dab' }
      ]),
    ];

    const borderColorList = [
      'rgba(0, 240, 255, 0.8)',
      'rgba(82, 196, 26, 0.8)',
      'rgba(255, 122, 69, 0.8)',
      'rgba(255, 197, 61, 0.8)',
      'rgba(179, 127, 235, 0.8)',
    ];

    const option = {
      backgroundColor: 'transparent',
     
      legend: {
        show: false,
      },
      graphic: [{
        type: 'text',
        left: 'center',
        top: '42%',
        style: {
          text: totalCount.toString(),
          textAlign: 'center',
          fill: '#00f0ff',
          fontSize: 28,
          fontWeight: 'bold',
          fontFamily: 'DIN Alternate, -apple-system, sans-serif',
          textShadowColor: 'rgba(0, 240, 255, 0.6)',
          textShadowBlur: 12,
        },
      }],
      series: [
        // 外圈装饰脉冲环
        {
          type: 'pie',
          radius: ['88%', '90%'],
          center: ['50%', '45%'],
          silent: true,
          label: { show: false },
          labelLine: { show: false },
          animation: false,
          data: [{
            value: 1,
            itemStyle: {
              color: 'rgba(0, 240, 255, 0.08)',
            },
          }],
        },
        // 中圈装饰虚线环
        {
          type: 'pie',
          radius: ['82%', '83%'],
          center: ['50%', '45%'],
          silent: true,
          label: { show: false },
          labelLine: { show: false },
          animation: false,
          data: [{
            value: 1,
            itemStyle: {
              color: 'transparent',
              borderWidth: 1,
              borderColor: 'rgba(0, 240, 255, 0.15)',
              borderType: 'dashed',
            },
          }],
        },
        // 主饼图
        {
          type: 'pie',
          radius: ['45%', '75%'],
          center: ['50%', '45%'],
          animationType: 'expansion',
          animationDuration: 1200,
          itemStyle: {
            borderRadius: 4,
            borderColor: 'rgba(10, 14, 26, 0.9)',
            borderWidth: 2,
            shadowBlur: 15,
            shadowColor: 'rgba(0, 0, 0, 0.4)',
          },
          label: {
            show: false,
          },
          labelLine: {
            show: false,
          },
          emphasis: {
            scale: true,
            scaleSize: 8,
            itemStyle: {
              shadowBlur: 40,
              shadowColor: 'rgba(0, 240, 255, 0.6)',
            },
          },
          data: chartData.map((item, index) => ({
            ...item,
            itemStyle: {
              color: colorList[index % colorList.length],
              borderColor: borderColorList[index % borderColorList.length],
              borderWidth: 2,
            },
          })),
        },
        // 内圈发光
        {
          type: 'pie',
          radius: ['40%', '42%'],
          center: ['50%', '45%'],
          silent: true,
          label: { show: false },
          labelLine: { show: false },
          animation: false,
          data: [{
            value: 1,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: 'rgba(0, 240, 255, 0.15)' },
                { offset: 0.5, color: 'rgba(0, 240, 255, 0.25)' },
                { offset: 1, color: 'rgba(0, 240, 255, 0.15)' },
              ]),
            },
          }],
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
  }, [reasons, totalCount]);

  // 自定义图例
  const colors = ['#00f0ff', '#52c41a', '#ff7a45', '#ffc53d', '#b37feb'];
  const legendData = (reasons.length > 0 ? reasons : [
    { name: '刑满释放', count: 0 },
    { name: '外出就医', count: 0 },
    { name: '外出教育', count: 0 },
    { name: '离监探亲', count: 0 },
    { name: '押回重审', count: 0 },
  ]);

  return (
    <div className="status-pie-chart" style={{ position: 'relative', zIndex: 1 }}>
      <div className="chart-title">
        <div className="title-content">
          <PieChartOutlined />
          <span>罪犯状态分布</span>
        </div>
        <div className="title-line"></div>
        <div className="title-decor">
          <span className="decor-dot"></span>
          <span className="decor-dot"></span>
          <span className="decor-dot"></span>
        </div>
      </div>
      <div className="chart-wrapper" style={{ position: 'relative', zIndex: 1 }}>
        <div ref={chartRef} className="echarts-container" style={{ position: 'relative', zIndex: 1 }} />
      </div>
      <div className="pie-legend">
        {legendData.map((item, i) => (
          <div key={i} className="pie-legend-item">
            <span className="legend-dot" style={{ background: colors[i % colors.length] }}></span>
            <span className="legend-name">{item.name}</span>
            <span className="legend-count">{item.count || 0}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StatusPieChart;
