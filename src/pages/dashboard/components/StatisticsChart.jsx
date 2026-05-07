import React, { useEffect, useRef, useState } from 'react';
import { LineChartOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';

const StatisticsChart = ({ data }) => {
  const chartRef = useRef(null);
  const [chartType, setChartType] = useState('month');

  useEffect(() => {
    if (!chartRef.current) return;

    const chart = echarts.init(chartRef.current);
    const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
    const quarters = ['Q1', 'Q2', 'Q3', 'Q4'];

    const prisons = data?.length > 0 ? data : [
      { month: '01', prisons: [{ name: '北京第一监狱', values: [65, 72, 68, 75, 80, 78, 82, 85, 79, 83, 88, 90] }, { name: '上海浦东监狱', values: [58, 62, 65, 70, 72, 75, 78, 80, 76, 82, 85, 88] }, { name: '广州番禺监狱', values: [70, 68, 72, 78, 82, 85, 88, 90, 87, 92, 95, 98] }] }
    ];

    const colors = ['#00f0ff', '#1877ff', '#52c41a', '#ff4d4f', '#faad14', '#722ed1', '#00cec8'];

    const xData = chartType === 'month' ? months : quarters;
    const seriesData = prisons.map((monthData, idx) => ({
      name: monthData.prison?.name || `监狱${idx + 1}`,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 2,
        color: colors[idx % colors.length]
      },
      itemStyle: {
        color: colors[idx % colors.length]
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: colors[idx % colors.length] + '40' },
          { offset: 1, color: colors[idx % colors.length] + '05' }
        ])
      },
      data: chartType === 'month'
        ? (monthData.prison?.values || Array(12).fill(0))
        : [
            (monthData.prison?.values?.[0] + monthData.prison?.values?.[1] + monthData.prison?.values?.[2]) / 3,
            (monthData.prison?.values?.[3] + monthData.prison?.values?.[4] + monthData.prison?.values?.[5]) / 3,
            (monthData.prison?.values?.[6] + monthData.prison?.values?.[7] + monthData.prison?.values?.[8]) / 3,
            (monthData.prison?.values?.[9] + monthData.prison?.values?.[10] + monthData.prison?.values?.[11]) / 3
          ].map(v => Math.round(v))
    }));

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(20, 25, 45, 0.9)',
        borderColor: 'rgba(0, 240, 255, 0.3)',
        textStyle: { color: '#fff' }
      },
      legend: {
        data: seriesData.map(s => s.name),
        textStyle: { color: 'rgba(255,255,255,0.7)' },
        top: 0
      },
      grid: {
        left: '5%',
        right: '5%',
        bottom: '10%',
        top: '25%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: xData,
        axisLine: { lineStyle: { color: 'rgba(0, 240, 255, 0.3)' } },
        axisLabel: { color: 'rgba(255,255,255,0.6)' }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
        axisLabel: { color: 'rgba(255,255,255,0.6)' }
      },
      series: seriesData
    };

    chart.setOption(option);

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [data, chartType]);

  return (
    <div className="statistics-chart">
      <div className="chart-header">
        <div className="chart-title">
          <LineChartOutlined />
          <span>出工统计</span>
        </div>
        <div className="chart-tabs">
          <button
            className={`tab-btn ${chartType === 'month' ? 'active' : ''}`}
            onClick={() => setChartType('month')}
          >
            月度
          </button>
          <button
            className={`tab-btn ${chartType === 'quarter' ? 'active' : ''}`}
            onClick={() => setChartType('quarter')}
          >
            季度
          </button>
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
