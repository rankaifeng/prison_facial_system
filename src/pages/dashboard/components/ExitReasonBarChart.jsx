import React, { useEffect, useRef } from 'react';
import { BarChartOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';

const ExitReasonBarChart = ({ data }) => {
  const chartRef = useRef(null);

  const reasons = data?.total?.reasons || [];

  useEffect(() => {
    if (!chartRef.current) return;

    const chart = echarts.init(chartRef.current);

    const chartData = reasons.length > 0 ? reasons.map(item => ({
      name: item.name,
      value: item.count || 0
    })) : [];

    const option = {
      backgroundColor: 'transparent',
      grid: {
        left: '5%',
        right: '5%',
        top: '15%',
        bottom: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: chartData.map(item => item.name),
        axisLabel: {
          color: 'rgba(255, 255, 255, 0.7)',
          fontSize: 10,
          interval: 0,
          rotate: 0
        },
        axisLine: {
          lineStyle: { color: 'rgba(0, 240, 255, 0.3)' }
        },
        axisTick: { show: false }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: 'rgba(255, 255, 255, 0.5)',
          fontSize: 10
        },
        splitLine: {
          lineStyle: { color: 'rgba(0, 240, 255, 0.1)' }
        },
        axisLine: { show: false },
        axisTick: { show: false }
      },
      series: [{
        type: 'bar',
        data: chartData.map((item, index) => ({
          value: item.value,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#00f0ff' },
              { offset: 1, color: 'rgba(0, 240, 255, 0.3)' }
            ]),
            borderRadius: [4, 4, 0, 0]
          }
        })),
        barWidth: '50%',
        label: {
          show: true,
          position: 'top',
          color: '#00f0ff',
          fontSize: 10,
          formatter: '{c}'
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#00f0ff' },
              { offset: 1, color: 'rgba(24, 119, 255, 0.5)' }
            ])
          }
        }
      }],
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(20, 25, 45, 0.95)',
        borderColor: 'rgba(0, 240, 255, 0.5)',
        borderWidth: 1,
        textStyle: { color: '#fff', fontSize: 12 },
        axisPointer: {
          type: 'shadow',
          shadowStyle: {
            color: 'rgba(0, 240, 255, 0.1)'
          }
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
        <div className="header-content">
          <BarChartOutlined />
          <span>出监类型统计</span>
        </div>
        <div className="header-line"></div>
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