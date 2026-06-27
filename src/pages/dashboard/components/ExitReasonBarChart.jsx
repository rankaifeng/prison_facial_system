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
      series: [{
        type: 'bar',
        data: chartData.map((item, index) => ({
          value: item.value,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#00f0ff' },
              { offset: 0.5, color: 'rgba(0, 180, 255, 0.8)' },
              { offset: 1, color: 'rgba(0, 80, 150, 0.6)' }
            ]),
            borderRadius: [6, 6, 0, 0]
          }
        })),
        barWidth: '55%',
        barGap: '30%',
        label: {
          show: true,
          position: 'top',
          distance: 8,
          color: '#00f0ff',
          fontSize: 12,
          fontWeight: 'bold',
          formatter: '{c}',
          textShadowColor: 'rgba(0, 240, 255, 0.8)',
          textShadowBlur: 8
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#00f0ff' },
              { offset: 0.5, color: 'rgba(24, 119, 255, 0.9)' },
              { offset: 1, color: 'rgba(0, 60, 180, 0.7)' }
            ])
          }
        },
        backgroundStyle: {
          color: 'rgba(0, 240, 255, 0.05)',
          borderRadius: [4, 4, 0, 0]
        },
        showBackground: true
      }],
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
        extraCssText: 'box-shadow: 0 0 20px rgba(0, 240, 255, 0.3);'
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