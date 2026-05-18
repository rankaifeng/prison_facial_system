import React, { useEffect, useRef } from 'react';
import { PieChartOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';

const StatusPieChart = ({ data }) => {
  const chartRef = useRef(null);

  // 从API获取的数据结构: data.total.reasons = [{name: '刑满释放', count: 100}, ...]
  const reasons = data?.total?.reasons || [];

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

    // 使用API返回的reasons数据，如果没有则用defaultData
    const chartData = reasons.length > 0 ? reasons.map(item => ({
      name: item.name,
      value: item.count || 0
    })) : defaultData;

    const colors = ['#1890ff', '#52c41a', '#ff4d4f', '#faad14', '#722ed1'];

    const option = {
      backgroundColor: 'transparent',
      // tooltip: {
      //   trigger: 'item',
      //   backgroundColor: 'rgba(20, 25, 45, 0.95)',
      //   borderColor: 'rgba(0, 240, 255, 0.5)',
      //   borderWidth: 1,
      //   textStyle: { color: '#fff' },
      //   formatter: '{b}: {c} ({d}%)',
      //   z: 9999,
      //   extraCssText: 'z-index: 9999; position: absolute;',
      // },
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
  }, [reasons]);

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
    </div>
  );
};

export default StatusPieChart;