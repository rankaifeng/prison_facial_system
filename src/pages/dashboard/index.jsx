import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Typography, Dropdown, ConfigProvider, Modal, Button, Menu } from 'antd';
import { SafetyOutlined, MenuOutlined, LogoutOutlined, FullscreenOutlined, FullscreenExitOutlined, SyncOutlined, CheckCircleOutlined, LoadingOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import LeftPanel from './components/LeftPanel';
import RightPanel from './components/RightPanel';
import StatisticsChart from './components/StatisticsChart';
import StatusPieChart from './components/StatusPieChart';
import PrisonMap from './components/PrisonMap';
import ExitConfirmModal from './components/ExitConfirmModal';
import ReturnConfirmModal from './components/ReturnConfirmModal';
import EnterConfirmModal from './components/EnterConfirmModal';
import OperationSelectModal from './components/OperationSelectModal';
import ExitReasonBarChart from './components/ExitReasonBarChart';
import { realtimeStatistics, sync, prisonMessages } from '@/api/globApi';
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
  const [enterModalStep, setEnterModalStep] = useState(0);
  const [selectModalOpen, setSelectModalOpen] = useState(false);
  const [activeOperation, setActiveOperation] = useState(null);
  const exitStepRef = useRef(0);
  const enterStepRef = useRef(0);
  const activeOpRef = useRef(null);
  const navigate = useNavigate();

  // 同步相关状态
  const [syncOpen, setSyncOpen] = useState(false);
  const [syncProgress, setSyncProgress] = useState(null);
  const [syncLoading, setSyncLoading] = useState(false);
  const syncPollRef = useRef(null);
  const messagesRef = useRef(null);

  const SYNC_STEPS = [
    { key: 'fetch_ids', label: '获取罪犯编号' },
    { key: 'sync_basic', label: '同步罪犯信息' },
    { key: 'sync_dahua', label: '同步到大华门禁' },
    { key: 'done', label: '完成' },
  ];

  // 同步 step 到 ref
  useEffect(() => {
    exitStepRef.current = exitModalStep;
  }, [exitModalStep]);

  useEffect(() => {
    enterStepRef.current = enterModalStep;
  }, [enterModalStep]);

  // 处理出监弹窗步骤变化
  const handleExitModalStepChange = useCallback((step) => {
    console.log('[前端] 出监弹窗步骤变化:', step);
    setExitModalStep(step);
    if (step === 0) {
      setPoliceFaceImage(null);
      setSwatFaceImage(null);
    } else if (step === 1) {
      setSwatFaceImage(null);
    } else if (step === 2) {
      setPoliceFaceImage(null);
    }
  }, []);

  // 处理入监弹窗步骤变化
  const handleEnterModalStepChange = useCallback((step) => {
    console.log('[前端] 入监弹窗步骤变化:', step);
    setEnterModalStep(step);
    if (step === 0) {
      setPoliceFaceImage(null);
    }
  }, []);

  const handleDoorEvent = useCallback((data) => {
    console.log('[前端] 收到WebSocket消息:', data.type, data.code, 'user_id:', data.user_id);

    if (data.type === 'door' && data.UserID) {
      console.log('[门禁] 识别到罪犯:', data.UserID);
      setActivePrisonerNo(data.UserID);
      setSelectModalOpen(true);
    } else if (data.type === 'face' && data.image_base64) {
      const b64 = data.image_base64;
      const img = 'data:image/jpeg;base64,' + b64;
      const op = activeOpRef.current;

      if (!op) {
        console.log('[前端] 未选择操作类型，跳过图片分配');
        return;
      }

      if (op === 'exit') {
        const step = exitStepRef.current;
        if (step === 1) {
          console.log('[智能事件] → 出监民警图片');
          setPoliceFaceImage(img);
          setSwatFaceImage(null);
        } else if (step === 2) {
          console.log('[智能事件] → 出监特警图片');
          setSwatFaceImage(img);
          setPoliceFaceImage(null);
        }
      } else if (op === 'enter') {
        const step = enterStepRef.current;
        if (step === 1) {
          console.log('[智能事件] → 入监民警图片');
          setPoliceFaceImage(img);
        }
      }
    }
  }, []);

  useDoorEvents({ onEvent: handleDoorEvent });

  const handleOperationSelect = useCallback((type) => {
    setSelectModalOpen(false);
    if (!type) return;

    setActiveOperation(type);
    activeOpRef.current = type;
    setPoliceFaceImage(null);
    setSwatFaceImage(null);

    if (type === 'exit') {
      setExitModalOpen(true);
    } else if (type === 'enter') {
      setEnterModalOpen(true);
    }
  }, []);

  const resetExitModal = useCallback(() => {
    setExitModalOpen(false);
    setPoliceFaceImage(null);
    setSwatFaceImage(null);
    setExitModalStep(0);
    setActiveOperation(null);
    activeOpRef.current = null;
  }, []);

  const resetEnterModal = useCallback(() => {
    setEnterModalOpen(false);
    setPoliceFaceImage(null);
    setEnterModalStep(0);
    setActiveOperation(null);
    activeOpRef.current = null;
  }, []);

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
    return () => {
      if (syncPollRef.current) clearInterval(syncPollRef.current);
    };
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
    if (typeof refreshMessages === 'function') {
      messagesRef.current = refreshMessages;
      refreshMessages();
    }
  }, []);

  // 同步相关函数
  const handleSyncStart = async () => {
    setSyncOpen(true);
    setSyncLoading(true);
    setSyncProgress({ state: 'PENDING', step: 'fetch_ids', percent: 0, message: '正在启动...', current: 0, total: 0 });
    try {
      const res = await sync.start();
      const taskId = res?.data?.task_id;
      if (taskId) {
        startPolling(taskId);
      }
    } catch (e) {
      setSyncProgress({ state: 'FAILURE', step: 'error', percent: 0, message: '启动失败: ' + (e.message || '未知错误'), current: 0, total: 0 });
    }
    setSyncLoading(false);
  };

  const startPolling = (taskId) => {
    if (syncPollRef.current) clearInterval(syncPollRef.current);
    syncPollRef.current = setInterval(async () => {
      try {
        const res = await sync.status(taskId);
        const data = res?.data;
        if (!data) return;
        setSyncProgress(data);
        if (data.state === 'SUCCESS' || data.state === 'FAILURE') {
          clearInterval(syncPollRef.current);
          syncPollRef.current = null;
          if (data.state === 'SUCCESS') {
            setTimeout(() => {
              setSyncOpen(false);
              fetchData();
              if (messagesRef.current) messagesRef.current();
            }, 1500);
          }
        }
      } catch (e) {
        console.error('查询同步状态失败:', e);
      }
    }, 1500);
  };

  const handleSyncClose = () => {
    if (syncPollRef.current) {
      clearInterval(syncPollRef.current);
      syncPollRef.current = null;
    }
    setSyncOpen(false);
    setSyncProgress(null);
  };

  const getStepStatus = (stepKey) => {
    if (!syncProgress) return 'wait';
    const stepOrder = ['fetch_ids', 'sync_basic', 'sync_dahua', 'done'];
    const currentIdx = stepOrder.indexOf(syncProgress.step);
    const targetIdx = stepOrder.indexOf(stepKey);
    if (syncProgress.state === 'FAILURE') {
      return targetIdx <= currentIdx ? (targetIdx === currentIdx ? 'error' : 'finish') : 'wait';
    }
    if (targetIdx < currentIdx) return 'finish';
    if (targetIdx === currentIdx) return syncProgress.state === 'SUCCESS' ? 'finish' : 'process';
    return 'wait';
  };

  const getStepIcon = (stepKey) => {
    const status = getStepStatus(stepKey);
    if (status === 'finish') return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} />;
    if (status === 'process') return <LoadingOutlined style={{ color: '#00f0ff', fontSize: 16 }} />;
    if (status === 'error') return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 16 }} />;
    return <ClockCircleOutlined style={{ color: 'rgba(255,255,255,0.25)', fontSize: 16 }} />;
  };

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
          <Title level={3} className="header-title">人员出入AB门人脸识别管理系统</Title>
        </div>
        <div className="header-center">
          <span className="welcome-greeting">{getGreeting()}，</span>
          <span className="welcome-name">{userName}</span>
        </div>
        <div className="header-right">
          <span className="current-time">{new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'long' })}</span>
          <span
            className="fullscreen-btn"
            onClick={toggleFullscreen}
          >
            {isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
          </span>
          {/* <span
            className="fullscreen-btn"
            onClick={handleSyncStart}
            title="同步数据"
          >
            <SyncOutlined />
          </span> */}
          <Dropdown overlay={
            <Menu onClick={navMenu.onClick}>
              {navMenu.items.map(item => (
                <Menu.Item key={item.key}>{item.label}</Menu.Item>
              ))}
            </Menu>
          } trigger={['click']}>
            <MenuOutlined className="nav-icon" />
          </Dropdown>
          <LogoutOutlined className="user-icon" onClick={handleLogout} />
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

      <OperationSelectModal
        visible={selectModalOpen}
        onSelect={handleOperationSelect}
        prisonerNo={activePrisonerNo}
      />
      <ExitConfirmModal
        visible={exitModalOpen}
        onCancel={resetExitModal}
        onOk={() => { resetExitModal(); handleDataUpdate(); }}
        prisonerNo={activePrisonerNo}
        policeFaceImage={policeFaceImage}
        swatFaceImage={swatFaceImage}
        onStepChange={handleExitModalStepChange}
      />
      <EnterConfirmModal
        visible={enterModalOpen}
        onCancel={resetEnterModal}
        onOk={() => { resetEnterModal(); handleDataUpdate(); }}
        prisonerNo={activePrisonerNo}
        policeFaceImage={policeFaceImage}
        onStepChange={handleEnterModalStepChange}
      />
      <ReturnConfirmModal
        visible={returnModalOpen}
        onCancel={() => setReturnModalOpen(false)}
        onOk={() => { setReturnModalOpen(false); handleDataUpdate(); }}
      />

      {/* 同步进度弹窗 */}
      <Modal
        visible={syncOpen}
        title={null}
        footer={null}
        onCancel={handleSyncClose}
        centered
        width={480}
        closable={syncProgress?.state !== 'PROGRESS'}
        maskClosable={syncProgress?.state !== 'PROGRESS'}
        bodyStyle={{ padding: '24px 28px' }}
      >
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <div style={{ fontSize: 18, fontWeight: 600, color: '#fff', marginBottom: 4 }}>
              数据同步
            </div>
            <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.45)' }}>
              从公安内网同步罪犯档案数据
            </div>
          </div>

          {/* 进度条 */}
          <div style={{ marginBottom: 24 }}>
            <div style={{
              height: 6,
              borderRadius: 3,
              background: 'rgba(255,255,255,0.08)',
              overflow: 'hidden',
            }}>
              <div style={{
                height: '100%',
                borderRadius: 3,
                width: `${syncProgress?.percent || 0}%`,
                background: syncProgress?.state === 'FAILURE'
                  ? 'linear-gradient(90deg, #ff4d4f, #ff7875)'
                  : 'linear-gradient(90deg, #00f0ff, #00b4d8)',
                transition: 'width 0.5s ease',
              }} />
            </div>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginTop: 8,
              fontSize: 12,
              color: 'rgba(255,255,255,0.45)',
            }}>
              <span>{syncProgress?.message || '等待中...'}</span>
              <span>{syncProgress?.percent || 0}%</span>
            </div>
          </div>

          {/* 步骤列表 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {SYNC_STEPS.map((step, idx) => {
              const status = getStepStatus(step.key);
              return (
                <div key={step.key} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '12px 16px',
                  borderRadius: 8,
                  background: status === 'process' ? 'rgba(0, 240, 255, 0.06)' : 'transparent',
                  border: status === 'process' ? '1px solid rgba(0, 240, 255, 0.15)' : '1px solid transparent',
                }}>
                  <div style={{ flexShrink: 0 }}>{getStepIcon(step.key)}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{
                      fontSize: 14,
                      color: status === 'process' ? '#00f0ff' : status === 'finish' ? '#52c41a' : status === 'error' ? '#ff4d4f' : 'rgba(255,255,255,0.35)',
                      fontWeight: status === 'process' ? 600 : 400,
                    }}>
                      {step.label}
                    </div>
                  </div>
                  {step.key === 'sync_basic' && status === 'process' && syncProgress?.total > 0 && (
                    <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)' }}>
                      {syncProgress.current}/{syncProgress.total}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* 完成/失败状态 */}
          {syncProgress?.state === 'SUCCESS' && (
            <div style={{
              textAlign: 'center',
              marginTop: 20,
              padding: '12px',
              borderRadius: 8,
              background: 'rgba(82, 196, 26, 0.1)',
              border: '1px solid rgba(82, 196, 26, 0.2)',
            }}>
              <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20, marginRight: 8 }} />
              <span style={{ color: '#52c41a', fontSize: 14 }}>{syncProgress.message}</span>
            </div>
          )}
          {syncProgress?.state === 'FAILURE' && (
            <div style={{
              textAlign: 'center',
              marginTop: 20,
              padding: '12px',
              borderRadius: 8,
              background: 'rgba(255, 77, 79, 0.1)',
              border: '1px solid rgba(255, 77, 79, 0.2)',
            }}>
              <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 20, marginRight: 8 }} />
              <span style={{ color: '#ff4d4f', fontSize: 14 }}>{syncProgress.message}</span>
            </div>
          )}
      </Modal>
    </div>
  );
};

export default Dashboard;