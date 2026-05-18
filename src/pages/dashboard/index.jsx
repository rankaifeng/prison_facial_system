import React, { useEffect, useState } from 'react';
import { Typography, Dropdown, ConfigProvider, theme, Modal, Button } from 'antd';
import { SafetyOutlined, MenuOutlined, LogoutOutlined, PlusOutlined, FullscreenOutlined, FullscreenExitOutlined, LoginOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import LeftPanel from './components/LeftPanel';
import RightPanel from './components/RightPanel';
import StatisticsChart from './components/StatisticsChart';
import StatusPieChart from './components/StatusPieChart';
import PrisonMap from './components/PrisonMap';
import ExitConfirmModal from './components/ExitConfirmModal';
import EnterConfirmModal from './components/EnterConfirmModal';
import ExitReasonBarChart from './components/ExitReasonBarChart';
import { realtimeStatistics } from '@/api/globApi';
import cache from '@/utils/cache';
import './index.less';

const { Title } = Typography;

const Dashboard = () => {
  const [realtimeData, setRealtimeData] = useState({});
  const [exitModalOpen, setExitModalOpen] = useState(false);
  const [enterModalOpen, setEnterModalOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const navigate = useNavigate();

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const realtime = await realtimeStatistics.get();
      console.log('实时统计数据:', realtime);
      setRealtimeData(realtime || {});
    } catch (error) {
      console.error('获取数据失败:', error);
    }
  };

  const navMenu = {
    items: [
      { key: '/dashboard', label: '首页大屏' },
      { key: '/prisoners', label: '档案库' },
      { key: '/statistics', label: '出监统计' },
      { key: '/return-records', label: '回监统计' },
      { key: '/permission', label: '账号管理' },
      { key: '/type-management', label: '类型管理' },
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
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setExitModalOpen(true)}
            className="exit-btn"
          >
            出监确认
          </Button>
          <Button
            type="primary"
            icon={<LoginOutlined />}
            onClick={() => setEnterModalOpen(true)}
            className="exit-btn"
          >
            入监确认
          </Button>
          <span className="current-time">{new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'long' })}</span>
          <span
            className="fullscreen-btn"
            onClick={toggleFullscreen}
          >
            {isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
          </span>
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
          <LeftPanel data={realtimeData} />
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
            <PrisonMap realtimeData={realtimeData} />
          </div>

          <div className="chart-section">
            <ExitReasonBarChart data={realtimeData} />
          </div>
        </div>

        <div className="right-area">
          <StatusPieChart data={realtimeData} />
          <RightPanel />
        </div>
      </div>

      <ExitConfirmModal
        open={exitModalOpen}
        onCancel={() => setExitModalOpen(false)}
        onOk={() => setExitModalOpen(false)}
      />
      <EnterConfirmModal
        open={enterModalOpen}
        onCancel={() => setEnterModalOpen(false)}
        onOk={() => setEnterModalOpen(false)}
      />
    </div>
  );
};

export default Dashboard;