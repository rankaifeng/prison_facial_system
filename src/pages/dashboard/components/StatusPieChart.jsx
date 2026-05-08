import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

const StatusPieChart = ({ data }) => {
  const chartRef = useRef(null);

  useEffect(() => {
    if (!chartRef.current) return;

    const chart = echarts.init(chartRef.current);

    const defaultData = [
      { name: '刑满释放', value: 680 },
      { name: '外出就医', value: 120 },
      { name: '外出教育', value: 25 },
      { name: '离监探亲', value: 15 },
      { name: '押回重审', value: 20 }
    ];

    const chartData = data && Object.keys(data).length > 0 ? [
      { name: '刑满释放', value: data.inPrison || 0 },
      { name: '外出就医', value: data.working || 0 },
      { name: '外出教育', value: data.hospital || 0 },
      { name: '离监探亲', value: data.isolated || 0 },
      { name: '押回重审', value: data.quarantine || 0 },
    ] : defaultData;

    const colors = ['#1890ff', '#52c41a', '#ff4d4f', '#faad14', '#722ed1'];

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(20, 25, 45, 0.95)',
        borderColor: 'rgba(0, 240, 255, 0.5)',
        borderWidth: 1,
        textStyle: { color: '#fff' },
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'horizontal',
        bottom: 0,
        textStyle: { color: 'rgba(255,255,255,0.7)', fontSize: 10 },
        itemWidth: 10,
        itemHeight: 10
      },
      series: [{
        type: 'pie',
        radius: ['40%', '80%'],
        center: ['50%', '45%'],
        depth: 45,
        animationType: 'expansion',
        animationDuration: 1500,
        animationEasing: 'elasticOut',
        animationDelay: (idx) => idx * 100,
        itemStyle: {
          borderRadius: 8,
          borderColor: 'rgba(20, 25, 45, 0.9)',
          borderWidth: 3,
          shadowBlur: 20,
          shadowColor: 'rgba(0, 0, 0, 0.6)'
        },
        label: {
          show: false
        },
        emphasis: {
          scale: true,
          scaleSize: 12,
          itemStyle: {
            shadowBlur: 35,
            shadowColor: 'rgba(0, 240, 255, 0.8)'
          }
        },
        data: chartData.map((item, index) => ({
          ...item,
          itemStyle: {
            color: colors[index % colors.length]
          }
        }))
      }]
    };
    chart.setOption(option);
    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [data]);

  return (
    <div className="status-pie-chart">
      <div className="chart-title">罪犯状态分布</div>
      <div className="chart-wrapper">
        <div ref={chartRef} className="echarts-container" />
      </div>
    </div>
  );
};

export default StatusPieChart;