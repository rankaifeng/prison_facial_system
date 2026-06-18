import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Typography, Dropdown, ConfigProvider, theme, Modal, Button } from 'antd';
import { SafetyOutlined, MenuOutlined, LogoutOutlined, FullscreenOutlined, FullscreenExitOutlined, LoginOutlined } from '@ant-design/icons';
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
import useDoorEvents from '@/hooks/useDoorEvents';
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
  const [activePrisonerNo, setActivePrisonerNo] = useState(null);
  const [policeFaceImage, setPoliceFaceImage] = useState(null);
  const [swatFaceImage, setSwatFaceImage] = useState(null);
  const [exitModalStep, setExitModalStep] = useState(0);
  const stepRef = useRef(0);
  const navigate = useNavigate();

  // 同步 step 到 ref
  useEffect(() => {
    stepRef.current = exitModalStep;
  }, [exitModalStep]);

  // 处理弹窗步骤变化
  const handleExitModalStepChange = useCallback((step) => {
    console.log('[前端] 弹窗步骤变化:', step);
    setExitModalStep(step);
    
    // 当步骤变化时，清理不再需要的图片
    if (step === 0) {
      // 重置到信息填写步骤，清理所有图片
      setPoliceFaceImage(null);
      setSwatFaceImage(null);
    } else if (step === 1) {
      // 进入民警确认步骤，清理特警图片（如果存在），保留民警图片
      setSwatFaceImage(null);
    } else if (step === 2) {
      // 进入特警确认步骤，清理民警图片（如果存在），保留特警图片
      setPoliceFaceImage(null);
    }
  }, []);

  const handleDoorEvent = useCallback((data) => {
    console.log('[前端] 收到WebSocket消息:', data.type, data.code, 'user_id:', data.user_id, 'step:', stepRef.current);
    
    if (data.type === 'door' && data.UserID) {
      // 门禁事件：罪犯识别
      console.log('[门禁] 识别到罪犯:', data.UserID);
      setActivePrisonerNo(data.UserID);
      setExitModalOpen(true);
    } else if (data.type === 'face' && data.image_base64) {
      // 人脸图片事件
      const b64 = data.image_base64;
      console.log('[智能事件] 收到图片 base64长度:', b64.length, 'user_id:', data.user_id, 'temp_id:', data.temp_id);
      
      // 检查是否是延迟的图片（超过3秒）
      const currentTime = Date.now();
      const eventTime = data.timestamp || currentTime;
      const delay = currentTime - eventTime;
      
      if (delay > 3000) {
        console.log('[智能事件] 跳过延迟图片，延迟:', delay, 'ms');
        return;
      }
      
      const img = 'data:image/jpeg;base64,' + b64;
      const currentStep = stepRef.current;
      
      // 检查图片是否应该分配给当前步骤
      // 只有当弹窗打开且处于目标步骤时，才分配图片
      if (!exitModalOpen) {
        console.log('[前端] 弹窗未打开，跳过图片分配');
        return;
      }
      
      // 民警确认步骤（步骤1）
      if (currentStep === 1) {
        console.log('[智能事件] → 民警图片(最新)');
        setPoliceFaceImage(img);
        // 清除特警图片，确保只显示当前步骤的图片
        setSwatFaceImage(null);
      }
      // 特警确认步骤（步骤2）
      else if (currentStep === 2) {
        console.log('[智能事件] → 特警图片(最新)');
        setSwatFaceImage(img);
        // 清除民警图片，确保只显示当前步骤的图片
        setPoliceFaceImage(null);
      } else {
        console.log('[智能事件] 当前步骤:', currentStep, '跳过图片分配');
      }
    } else if (data.type === 'metadata' && data.user_id) {
      // 元数据事件（用于调试）
      console.log('[智能事件] 收到元数据 user_id:', data.user_id, 'code:', data.code);
    } else {
      console.log('[前端] 未知消息类型或缺少数据:', data);
    }
  }, [exitModalOpen]);

  useDoorEvents({ onEvent: handleDoorEvent });

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
            <Button
              type="primary"
              icon={<LoginOutlined />}
              onClick={() => setEnterModalOpen(true)}
              className="exit-btn"
            >
              入监确认
            </Button>
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
        onCancel={() => { setExitModalOpen(false); setPoliceFaceImage(null); setSwatFaceImage(null); setExitModalStep(0); }}
        onOk={() => { setExitModalOpen(false); setPoliceFaceImage(null); setSwatFaceImage(null); setExitModalStep(0); handleDataUpdate(); }}
        prisonerNo={activePrisonerNo}
        policeFaceImage={policeFaceImage}
        swatFaceImage={swatFaceImage}
        onStepChange={handleExitModalStepChange}
      />
      <EnterConfirmModal
        open={enterModalOpen}
        onCancel={() => setEnterModalOpen(false)}
        onOk={() => { setEnterModalOpen(false); handleDataUpdate(); }}
        prisonerNo="5155016879"
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