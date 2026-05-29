import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Typography, Dropdown, ConfigProvider, theme, Modal, Button } from 'antd';
import { SafetyOutlined, MenuOutlined, LogoutOutlined, PlusOutlined, FullscreenOutlined, FullscreenExitOutlined, LoginOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import LeftPanel from './components/LeftPanel';
import RightPanel from './components/RightPanel';
import StatisticsChart from './components/StatisticsChart';
import StatusPieChart from './components/StatusPieChart';
import PrisonMap from './components/PrisonMap';
import ExitConfirmModal from './components/ExitConfirmModal';
import ReturnConfirmModal from './components/ReturnConfirmModal';
import EnterConfirmModal from './components/EnterConfirmModal';
import ExitReasonBarChart from './components/ExitReasonBarChart';
import { realtimeStatistics } from '@/api/globApi';
import cache from '@/utils/cache';
import './index.less';

const { Title } = Typography;

const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 6) return '凌晨好';
  if (hour < 9) return '早上好';
  if (hour < 12) return '上午好';
  if (hour < 14) return '中午好';
  if (hour < 18) return '下午好';
  if (hour < 22) return '晚上好';
  return '夜里好';
};

const Dashboard = () => {
  const [realtimeData, setRealtimeData] = useState({});
  const [exitModalOpen, setExitModalOpen] = useState(false);
  const [returnModalOpen, setReturnModalOpen] = useState(false);
  const [enterModalOpen, setEnterModalOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [userName, setUserName] = useState('');
  const [isAdmin, setIsAdmin] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const storedPrisonName = cache.getVal('prisonName');
    setUserName(storedPrisonName || '管理员');
    setIsAdmin(!storedPrisonName);
  }, []);

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
      setRealtimeData(realtime || {});
    } catch (error) {
      console.error('获取数据失败:', error);
    }
  };

  const handleDataUpdate = useCallback((refreshMessages) => {
    fetchData();
    if (refreshMessages) {
      refreshMessages();
    }
  }, []);

  const navMenu = {
    items: isAdmin ? [
      { key: '/dashboard', label: '首页大屏' },
      { key: '/prisoners', label: '档案库' },
      { key: '/statistics', label: '出监记录' },
      { key: '/return-records', label: '回监记录' },
      { key: '/permission', label: '账号管理' },
      { key: '/type-management', label: '出监原因管理' },
    ] : [
      { key: '/dashboard', label: '首页大屏' },
      { key: '/prisoners', label: '档案库' },
      { key: '/statistics', label: '出监记录' },
      { key: '/return-records', label: '回监记录' },
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
        <div className="header-center">
          <span className="welcome-greeting">{getGreeting()}，</span>
          <span className="welcome-name">{userName}</span>
        </div>
        <div className="header-right">
          {isAdmin && (
            <>
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
                onClick={() => setReturnModalOpen(true)}
                className="exit-btn"
              >
                回监确认
              </Button>
            </>
          )}
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
                <span>{isAdmin ? '监狱概览' : userName}</span>
              </div>
              <div className="title-line"></div>
              <div className="title-decor">
                <span className="decor-dot"></span>
                <span className="decor-dot"></span>
                <span className="decor-dot"></span>
              </div>
            </div>
            <PrisonMap realtimeData={realtimeData} isAdmin={isAdmin} />
          </div>

          <div className="chart-section">
            <ExitReasonBarChart data={realtimeData} />
          </div>
        </div>

        <div className="right-area">
          <StatusPieChart data={realtimeData} />
          <RightPanel onDataUpdate={handleDataUpdate} />
        </div>
      </div>

      <ExitConfirmModal
        open={exitModalOpen}
        onCancel={() => setExitModalOpen(false)}
        onOk={() => { setExitModalOpen(false); handleDataUpdate(); }}
      />
      <EnterConfirmModal
        open={enterModalOpen}
        onCancel={() => setEnterModalOpen(false)}
        onOk={() => { setEnterModalOpen(false); handleDataUpdate(); }}
      />
      <ReturnConfirmModal
        open={returnModalOpen}
        onCancel={() => setReturnModalOpen(false)}
        onOk={() => { setReturnModalOpen(false); handleDataUpdate(); }}
      />
    </div>
  );
};

export default Dashboard;