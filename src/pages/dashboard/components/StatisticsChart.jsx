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

    const defaultData = [
      { month: '01', prisons: [{ name: '第一监狱', value: 85 }, { name: '第二监狱', value: 72 }, { name: '第三监狱', value: 95 }, { name: '第四监狱', value: 68 }] },
      { month: '02', prisons: [{ name: '第一监狱', value: 92 }, { name: '第二监狱', value: 78 }, { name: '第三监狱', value: 88 }, { name: '第四监狱', value: 75 }] },
      { month: '03', prisons: [{ name: '第一监狱', value: 88 }, { name: '第二监狱', value: 82 }, { name: '第三监狱', value: 92 }, { name: '第四监狱', value: 72 }] },
      { month: '04', prisons: [{ name: '第一监狱', value: 90 }, { name: '第二监狱', value: 85 }, { name: '第三监狱', value: 96 }, { name: '第四监狱', value: 78 }] },
      { month: '05', prisons: [{ name: '第一监狱', value: 95 }, { name: '第二监狱', value: 88 }, { name: '第三监狱', value: 98 }, { name: '第四监狱', value: 82 }] },
      { month: '06', prisons: [{ name: '第一监狱', value: 92 }, { name: '第二监狱', value: 90 }, { name: '第三监狱', value: 95 }, { name: '第四监狱', value: 80 }] },
      { month: '07', prisons: [{ name: '第一监狱', value: 98 }, { name: '第二监狱', value: 92 }, { name: '第三监狱', value: 100 }, { name: '第四监狱', value: 85 }] },
      { month: '08', prisons: [{ name: '第一监狱', value: 95 }, { name: '第二监狱', value: 90 }, { name: '第三监狱', value: 98 }, { name: '第四监狱', value: 88 }] },
      { month: '09', prisons: [{ name: '第一监狱', value: 92 }, { name: '第二监狱', value: 88 }, { name: '第三监狱', value: 96 }, { name: '第四监狱', value: 85 }] },
      { month: '10', prisons: [{ name: '第一监狱', value: 96 }, { name: '第二监狱', value: 92 }, { name: '第三监狱', value: 99 }, { name: '第四监狱', value: 90 }] },
      { month: '11', prisons: [{ name: '第一监狱', value: 98 }, { name: '第二监狱', value: 95 }, { name: '第三监狱', value: 100 }, { name: '第四监狱', value: 92 }] },
      { month: '12', prisons: [{ name: '第一监狱', value: 100 }, { name: '第二监狱', value: 98 }, { name: '第三监狱', value: 100 }, { name: '第四监狱', value: 95 }] }
    ];

    const chartData = data?.length > 0 ? data : defaultData;
    const colors = ['#00f0ff', '#1877ff', '#52c41a', '#ff4d4f', '#faad14', '#722ed1', '#00cec8'];

    const xData = chartType === 'month' ? months : quarters;

    const prisonNames = chartData[0]?.prisons?.map(p => p.name);

    const seriesData = prisonNames.map((prisonName, idx) => {
      const monthlyValues = chartData.map(monthData => {
        const prison = monthData.prisons?.find(p => p.name === prisonName);
        return prison?.value || 0;
      });

      const quarterlyValues = [
        (monthlyValues[0] + monthlyValues[1] + monthlyValues[2]) / 3,
        (monthlyValues[3] + monthlyValues[4] + monthlyValues[5]) / 3,
        (monthlyValues[6] + monthlyValues[7] + monthlyValues[8]) / 3,
        (monthlyValues[9] + monthlyValues[10] + monthlyValues[11]) / 3
      ].map(v => Math.round(v));

      const color = colors[idx % colors.length];

      return {
        name: prisonName,
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: {
          width: 2,
          color: color
        },
        itemStyle: {
          color: color,
          shadowBlur: 10,
          shadowColor: color
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: color + '40' },
            { offset: 1, color: color + '05' }
          ])
        },
        data: chartType === 'month' ? monthlyValues : quarterlyValues
      };
    });

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(20, 25, 45, 0.95)',
        borderColor: 'rgba(0, 240, 255, 0.5)',
        borderWidth: 1,
        textStyle: { color: '#fff' },
        zlevel: 1000,
        z: 1000
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
        boundaryGap: false,
        data: xData,
        axisLine: { lineStyle: { color: 'rgba(0, 240, 255, 0.3)' } },
        axisLabel: { color: 'rgba(255,255,255,0.6)' },
        splitLine: { show: false }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        splitLine: { show: false },
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
        <div className="header-content">
          <LineChartOutlined />
          <span>出工统计</span>
        </div>
        <div className="header-line"></div>
        <div className="header-decor">
          <span className="decor-dot"></span>
          <span className="decor-dot"></span>
          <span className="decor-dot"></span>
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
