import React, { useEffect, useState } from 'react';
import { Typography, Dropdown, ConfigProvider, theme, Modal } from 'antd';
import { SafetyOutlined, MenuOutlined, LogoutOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import LeftPanel from './components/LeftPanel';
import RightPanel from './components/RightPanel';
import StatisticsChart from './components/StatisticsChart';
import StatusPieChart from './components/StatusPieChart';
import PrisonMap from './components/PrisonMap';
import { prison, realtimeStatistics, workStatistics, message as messageApi } from '@/api/globApi';
import cache from '@/utils/cache';
import './index.less';

const { Title } = Typography;

const Dashboard = () => {
  const [prisons, setPrisons] = useState([]);
  const [realtimeData, setRealtimeData] = useState({});
  const [prisonStats, setPrisonStats] = useState({});
  const [workData, setWorkData] = useState([]);
  const [messages, setMessages] = useState([]);
  const navigate = useNavigate();

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

  const navMenu = {
    items: [
      { key: '/dashboard', label: '首页大屏' },
      { key: '/prisoners', label: '档案库' },
      { key: '/statistics', label: '统计信息' },
      { key: '/permission', label: '权限管理' },
    ],
    onClick: ({ key }) => navigate(key),
  };

  const handleLogout = () => {
    Modal.confirm({
      title: '确认退出',
      content: '确定要退出登录吗？',
      okText: '确认',
      cancelText: '取消',
      onOk: () => {
        cache.clearVal();
        navigate('/login');
      },
    });
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="header-left">
          <SafetyOutlined className="header-icon" />
          <Title level={3} className="header-title">监狱关押罪犯出入管控平台</Title>
        </div>
        <div className="header-right">
          <span className="current-time">{new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'long' })}</span>
          <ConfigProvider
            theme={{
              algorithm: theme.darkAlgorithm,
              token: {
                colorPrimary: '#00f0ff',
                colorBgElevated: 'rgba(20, 25, 45, 0.95)',
                colorBgContainer: 'rgba(20, 25, 45, 0.95)',
              },
              components: {
                Dropdown: {
                  colorBgElevated: 'rgba(20, 25, 45, 0.95)',
                  colorPrimary: '#00f0ff',
                  controlItemBgHover: 'rgba(0, 240, 255, 0.1)',
                  controlItemBgActive: 'rgba(0, 240, 255, 0.2)',
                  colorBorder: 'rgba(0, 240, 255, 0.3)',
                  borderRadius: 8,
                  paddingInline: 16,
                },
              },
            }}
          >
            <Dropdown menu={navMenu} trigger={['click']}>
              <MenuOutlined className="nav-icon" />
            </Dropdown>
            <LogoutOutlined className="user-icon" onClick={handleLogout} />
          </ConfigProvider>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="left-area">
          <LeftPanel
            realtimeData={realtimeData}
            prisonStats={prisonStats}
            genderData={{ male: 680, female: 210 }}
          />
        </div>

        <div className="center-area">
          <div className="prisons-section">
            <div className="section-title">
              <div className="title-content">
                <SafetyOutlined />
                <span>监狱概览</span>
              </div>
              <div className="title-line"></div>
              <div className="title-decor">
                <span className="decor-dot"></span>
                <span className="decor-dot"></span>
                <span className="decor-dot"></span>
              </div>
            </div>
            <PrisonMap />
          </div>

          <div className="chart-section">
            <StatisticsChart data={workData} />
          </div>
        </div>

        <div className="right-area">
          <StatusPieChart data={prisonStats} />
          <RightPanel messages={messages} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;