import React, { useEffect, useState } from 'react';
import { Typography } from 'antd';
import { SafetyOutlined, ClockCircleOutlined } from '@ant-design/icons';
import PrisonCard from './components/PrisonCard';
import LeftPanel from './components/LeftPanel';
import RightPanel from './components/RightPanel';
import StatisticsChart from './components/StatisticsChart';
import { prison, realtimeStatistics, workStatistics, message as messageApi } from '@/api/globApi';
import './index.less';

const { Title, Text } = Typography;

const Dashboard = () => {
  const [prisons, setPrisons] = useState([]);
  const [realtimeData, setRealtimeData] = useState({});
  const [prisonStats, setPrisonStats] = useState({});
  const [workData, setWorkData] = useState([]);
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [prisonList, realtime, workStat, msgList] = await Promise.all([
        prison.list(),
        realtimeStatistics.get(),
        workStatistics.list(),
        messageApi.list({ limit: 10 }),
      ]);

      setPrisons(prisonList || []);
      setRealtimeData(realtime || {});
      setPrisonStats(realtime?.stats || {});
      setWorkData(workStat || []);
      setMessages(msgList || []);
    } catch (error) {
      console.error('获取数据失败:', error);
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="header-left">
          <SafetyOutlined className="header-icon" />
          <Title level={3} className="header-title">监狱关押罪犯出入管控平台</Title>
        </div>
        <div className="header-right">
          <ClockCircleOutlined />
          <span className="current-time">{new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'long' })}</span>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="left-area">
          <LeftPanel realtimeData={realtimeData} prisonStats={prisonStats} />
        </div>

        <div className="center-area">
          <div className="prisons-grid">
            {prisons.length > 0 ? (
              prisons.map((p, index) => (
                <PrisonCard
                  key={p.id || index}
                  name={p.name || `监狱${index + 1}`}
                  totalCount={p.totalCount || 0}
                  workCount={p.workCount || 0}
                  imageUrl={p.imageUrl}
                />
              ))
            ) : (
              <>
                {['第一监狱', '第二监狱', '第三监狱', '第四监狱', '第五监狱', '第六监狱', '第七监狱'].map((name, index) => (
                  <PrisonCard
                    key={index}
                    name={name}
                    totalCount={Math.floor(Math.random() * 500) + 200}
                    workCount={Math.floor(Math.random() * 300) + 100}
                  />
                ))}
              </>
            )}
          </div>

          <div className="bottom-area">
            <StatisticsChart data={workData} />
          </div>
        </div>

        <div className="right-area">
          <RightPanel messages={messages} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;