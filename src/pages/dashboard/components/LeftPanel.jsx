import React, { useEffect, useRef } from 'react';
import { UserOutlined, HeartOutlined, MedicineBoxOutlined, LockOutlined, DisconnectOutlined, HomeOutlined, ThunderboltOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';

const LeftPanel = ({ realtimeData, prisonStats }) => {
  const pieChartRef = useRef(null);

  useEffect(() => {
    if (!pieChartRef.current) return;

    const chart = echarts.init(pieChartRef.current);

    const total = realtimeData?.total || 890;
    const inPrison = prisonStats?.inPrison || 680;

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(20, 25, 45, 0.9)',
        borderColor: 'rgba(0, 240, 255, 0.3)',
        textStyle: { color: '#fff' },
        formatter: '{b}: {c} ({d}%)'
      },
      series: [{
        type: 'pie',
        radius: ['50%', '75%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        label: {
          show: true,
          position: 'center',
          formatter: () => `{val|${total}}`,
          rich: {
            val: {
              fontSize: 28,
              fontWeight: 'bold',
              color: '#fff',
              lineHeight: 36
            }
          }
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 28,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          {
            value: inPrison,
            name: '在监',
            itemStyle: { color: '#1890ff' }
          },
          {
            value: total - inPrison,
            name: '其他',
            itemStyle: { color: 'rgba(255,255,255,0.1)' }
          }
        ]
      }]
    };

    chart.setOption(option);

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [realtimeData, prisonStats]);

  return (
    <div className="left-panel">
      <div className="panel-section total-section">
        <div className="chart-header">
          <UserOutlined />
          <span>实时在监总人数</span>
        </div>
        <div className="chart-wrapper">
          <div ref={pieChartRef} className="echarts-container" />
        </div>
      </div>

      <div className="panel-section stats-section">
        <div className="section-header">
          <span>监狱罪犯情况</span>
        </div>
        <div className="stats-grid">
          <div className="stat-box">
            <div className="stat-icon in-prison">
              <UserOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">在监</div>
              <div className="stat-number">{prisonStats?.inPrison || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon working">
              <ThunderboltOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">出工</div>
              <div className="stat-number">{prisonStats?.working || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon hospital">
              <MedicineBoxOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">住院</div>
              <div className="stat-number">{prisonStats?.hospital || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon isolated">
              <LockOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">禁闭</div>
              <div className="stat-number">{prisonStats?.isolated || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon quarantine">
              <DisconnectOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">隔离</div>
              <div className="stat-number">{prisonStats?.quarantine || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon visiting">
              <HomeOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">探亲</div>
              <div className="stat-number">{prisonStats?.visiting || 0}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon punishment">
              <HeartOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">惩戒</div>
              <div className="stat-number">{prisonStats?.punishment || 0}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeftPanel;