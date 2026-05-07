import React, { useEffect, useState } from 'react';
import { Typography, Dropdown, ConfigProvider, theme } from 'antd';
import { SafetyOutlined, MenuOutlined, UserOutlined, SettingOutlined, LogoutOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import LeftPanel from './components/LeftPanel';
import RightPanel from './components/RightPanel';
import StatisticsChart from './components/StatisticsChart';
import StatusPieChart from './components/StatusPieChart';
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
      { key: '/exit-records', label: '出监记录' },
      { key: '/permission', label: '权限管理' },
    ],
    onClick: ({ key }) => navigate(key),
  };

  const userMenu = {
    items: [
      { key: 'changePwd', icon: <SettingOutlined />, label: '修改密码' },
      { type: 'divider' },
      { key: 'logout', icon: <LogoutOutlined />, label: '退出登录' },
    ],
    onClick: ({ key }) => {
      if (key === 'logout') {
        cache.clearVal();
        navigate('/login');
      }
    },
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
            <Dropdown menu={userMenu} trigger={['click']}>
              <UserOutlined className="user-icon" />
            </Dropdown>
          </ConfigProvider>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="left-area">
          <LeftPanel realtimeData={realtimeData} prisonStats={prisonStats} />
        </div>

        <div className="center-area">
          <div className="prisons-section">
            <div className="section-title">监狱概览</div>
            <div className="prison-img-container" />
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