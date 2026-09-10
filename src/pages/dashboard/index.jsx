import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Typography, Dropdown, ConfigProvider, Modal, Button, Menu } from 'antd';
import { SafetyOutlined, MenuOutlined, LogoutOutlined, LoginOutlined, FullscreenOutlined, FullscreenExitOutlined, SyncOutlined, DashboardOutlined, DatabaseOutlined, FileTextOutlined, SwapOutlined, UserOutlined, TagsOutlined } from '@ant-design/icons';
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
import HandheldSyncModal from './components/HandheldSyncModal';
import { realtimeStatistics, prisonMessages, archive } from '@/api/globApi';
import jinghuiImg from '@/imgs/jinghui.png';
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
  const [policeFaceName, setPoliceFaceName] = useState(null);
  const [swatFaceName, setSwatFaceName] = useState(null);
  const [capturedFaceImage, setCapturedFaceImage] = useState(null);
  const [archiveFaceImage, setArchiveFaceImage] = useState(null);
  const [exitModalStep, setExitModalStep] = useState(0);
  const [enterModalStep, setEnterModalStep] = useState(0);
  const [selectModalOpen, setSelectModalOpen] = useState(false);
  const [activeOperation, setActiveOperation] = useState(null);
  const exitStepRef = useRef(0);
  const enterStepRef = useRef(0);
  const activeOpRef = useRef(null);
  const navigate = useNavigate();
  const messagesRef = useRef(null);
  const [handheldSyncOpen, setHandheldSyncOpen] = useState(false);
  // 防止手持终端重复回调导致多次弹窗（同一人5秒内只弹一次）
  const lastFaceEventRef = useRef({ personId: '', time: 0 });

  // 处理出监弹窗步骤变化（同步更新 ref，确保抓拍事件能读到当前步骤）
  const handleExitModalStepChange = useCallback((step) => {
    setExitModalStep(step);
    exitStepRef.current = step;
    if (step === 0) {
      setPoliceFaceImage(null);
      setSwatFaceImage(null);
      setPoliceFaceName(null);
      setSwatFaceName(null);
    } else if (step === 1) {
      setSwatFaceImage(null);
      setSwatFaceName(null);
    } else if (step === 2) {
      setPoliceFaceImage(null);
      setPoliceFaceName(null);
    }
  }, []);

  // 处理入监弹窗步骤变化（同步更新 ref）
  const handleEnterModalStepChange = useCallback((step) => {
    setEnterModalStep(step);
    enterStepRef.current = step;
    if (step === 0) {
      setPoliceFaceImage(null);
      setPoliceFaceName(null);
    }
  }, []);

  const handleDoorEvent = useCallback((data) => {
    console.log("data", data);

    if (data.type === 'door' && data.UserID) {
      setActivePrisonerNo(data.UserID);
      setSelectModalOpen(true);
      // 主动获取档案照片，避免弹窗打开时没有照片
      archive.detail({ prisoner_no: data.UserID }).then(res => {
        if (res.code === 1 && res?.data?.mtxx?.length) {
          const photoUrl = res.data.mtxx[0].xp;
          if (photoUrl) setArchiveFaceImage(photoUrl);
        }
      }).catch(() => { });
      if (data.image_base64) {
        const img = 'data:image/jpeg;base64,' + data.image_base64;
        setCapturedFaceImage(img);
      }
    } else if (data.type === 'prisoner_face') {
      // 罪犯识别事件（大华门禁或手持终端）
      // 防抖：同一人5秒内只处理一次（设备会多次回调）
      const prisonerNoForDedup = data.user_id || data.prisoner_no || '';
      const now = Date.now();
      if (prisonerNoForDedup && prisonerNoForDedup === lastFaceEventRef.current.personId
          && now - lastFaceEventRef.current.time < 5000) {
        console.log('[前端] 忽略重复回调:', prisonerNoForDedup);
        return;
      }
      lastFaceEventRef.current = { personId: prisonerNoForDedup, time: now };

      console.log('[前端] 收到 prisoner_face 事件:', data);
      console.log('[前端] user_id:', data.user_id, 'prisoner_no:', data.prisoner_no);
      console.log('[前端] image_base64 长度:', data.image_base64?.length || 0);
      console.log('[前端] archive_image_base64 长度:', data.archive_image_base64?.length || 0);

      const prisonerNo = data.user_id || data.prisoner_no || '';
      if (prisonerNo) {
        console.log('[前端] 设置罪犯编号:', prisonerNo);
        setActivePrisonerNo(prisonerNo);
        setSelectModalOpen(true);
        // 获取档案照片
        archive.detail({ prisoner_no: prisonerNo }).then(res => {
          console.log('[前端] 档案详情返回:', res);
          if (res?.code === 1 && res?.data?.mtxx?.length) {
            const photoUrl = res.data.mtxx[0].xp;
            console.log('[前端] 档案照片URL:', photoUrl);
            if (photoUrl) setArchiveFaceImage(photoUrl);
          }
        }).catch(err => {
          console.error('[前端] 获取档案详情失败:', err);
        });
      }
      // 设置终端抓拍照片
      if (data.image_base64) {
        const img = 'data:image/jpeg;base64,' + data.image_base64;
        console.log('[前端] 设置抓拍照片, 长度:', img.length);
        setCapturedFaceImage(img);
      } else {
        console.log('[前端] 没有抓拍照片数据');
      }
      // 如果有档案照片（大华返回的）
      if (data.archive_image_base64) {
        const img = 'data:image/jpeg;base64,' + data.archive_image_base64;
        console.log('[前端] 设置档案照片(base64), 长度:', img.length);
        setArchiveFaceImage(img);
      } else {
        console.log('[前端] 没有档案照片(base64)数据');
      }
    } else if (data.type === 'face' && data.image_base64) {
      // 民警/特警抓拍（来自 10.2.48.223）
      const b64 = data.image_base64;
      const img = 'data:image/jpeg;base64,' + b64;
      const faceName = data.user_name || null;
      const op = activeOpRef.current;

      if (!op) {
        return;
      }

      if (op === 'exit') {
        const step = exitStepRef.current;
        if (step === 1) {
          setPoliceFaceImage(img);
          setPoliceFaceName(faceName);
          setSwatFaceImage(null);
          setSwatFaceName(null);
        } else if (step === 2) {
          setSwatFaceImage(img);
          setSwatFaceName(faceName);
          setPoliceFaceImage(null);
          setPoliceFaceName(null);
        }
      } else if (op === 'enter') {
        const step = enterStepRef.current;
        if (step === 1) {
          setPoliceFaceImage(img);
          setPoliceFaceName(faceName);
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
    } else if (type === 'return') {
      setReturnModalOpen(true);
    }
  }, []);

  const resetExitModal = useCallback(() => {
    setExitModalOpen(false);
    setPoliceFaceImage(null);
    setSwatFaceImage(null);
    setCapturedFaceImage(null);
    setArchiveFaceImage(null);
    setExitModalStep(0);
    setActiveOperation(null);
    activeOpRef.current = null;
  }, []);

  const resetEnterModal = useCallback(() => {
    setEnterModalOpen(false);
    setPoliceFaceImage(null);
    setCapturedFaceImage(null);
    setArchiveFaceImage(null);
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
    }
  };

  const handleDataUpdate = useCallback((refreshMessages) => {
    fetchData();
    if (typeof refreshMessages === 'function') {
      messagesRef.current = refreshMessages;
      refreshMessages();
    } else if (typeof messagesRef.current === 'function') {
      messagesRef.current();
    }
  }, []);

  const navMenu = {
    items: isAdmin ? [
      { key: '/dashboard', label: '首页大屏', icon: <DashboardOutlined /> },
      { key: '/prisoners', label: '档案库', icon: <DatabaseOutlined /> },
      { key: '/statistics', label: '出监记录', icon: <FileTextOutlined /> },
      { key: '/return-records', label: '回监记录', icon: <SwapOutlined /> },
      { key: '/permission', label: '账号管理', icon: <UserOutlined /> },
      { key: '/type-management', label: '出监原因管理', icon: <TagsOutlined /> },
    ] : [
      { key: '/dashboard', label: '首页大屏', icon: <DashboardOutlined /> },
      { key: '/prisoners', label: '档案库', icon: <DatabaseOutlined /> },
      { key: '/statistics', label: '出监记录', icon: <FileTextOutlined /> },
      { key: '/return-records', label: '回监记录', icon: <SwapOutlined /> },
    ],
    onClick: ({ key }) => navigate(key),
  };

  const handleLogout = () => {
    Modal.confirm({
      title: '确认退出',
      content: '确定要退出登录吗？',
      okText: '确认',
      cancelText: '取消',
      className: 'dashboard-dark-modal',
      onOk: () => {
        cache.clearVal();
        navigate('/login');
      },
    });
  };

  const handleHandheldSync = useCallback(() => {
    setHandheldSyncOpen(true);
  }, []);

  return (
    <div className="dashboard">
      <div className="dashboard-scan-beam"></div>
      <div className="dashboard-header">
        <div className="header-left">
          <div className="header-logo">
            <img src={jinghuiImg} alt="警徽" style={{ width: 36, height: 36, borderRadius: '50%' }} />
          </div>
          <Title level={3} className="header-title">罪犯进出AB门人脸识别系统</Title>
        </div>
        <div className="header-center" style={{ visibility: 'hidden' }}>
          <span className="welcome-greeting">{getGreeting()}，</span>
          <span className="welcome-name">{userName}</span>
        </div>
        <div className="header-right">
          <Button className="exit-btn" icon={<LogoutOutlined />} onClick={() => setExitModalOpen(true)}>出监确认</Button>
          <Button className="exit-btn" icon={<LoginOutlined />} onClick={() => setReturnModalOpen(true)}>回监确认</Button>
          <Button className="exit-btn" icon={<SyncOutlined />} onClick={handleHandheldSync} title="同步罪犯到手持终端">同步</Button>
          <span
            className="fullscreen-btn"
            onClick={toggleFullscreen}
          >
            {isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
          </span>
          <Dropdown
            menu={{
              items: navMenu.items.map(item => ({
                key: item.key,
                icon: item.icon,
                label: item.label,
              })),
              onClick: navMenu.onClick,
              className: 'dashboard-dark-menu',
            }}
            trigger={['click']}
            dropdownRender={(menu) => (
              <div style={{ background: 'rgba(14, 18, 35, 1)', border: '1px solid rgba(0, 240, 255, 0.3)', borderRadius: 8, overflow: 'hidden' }}>
                {menu}
              </div>
            )}
          >
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
            <div className="corner-decor top-left"></div>
            <div className="corner-decor top-right"></div>
            <div className="corner-decor bottom-left"></div>
            <div className="corner-decor bottom-right"></div>
            <div className="grid-overlay"></div>
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
            <div className="corner-decor top-left"></div>
            <div className="corner-decor top-right"></div>
            <div className="corner-decor bottom-left"></div>
            <div className="corner-decor bottom-right"></div>
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
        policeFaceName={policeFaceName}
        swatFaceName={swatFaceName}
        capturedFaceImage={capturedFaceImage}
        archiveFaceImage={archiveFaceImage}
        onStepChange={handleExitModalStepChange}
      />
      <EnterConfirmModal
        visible={enterModalOpen}
        onCancel={resetEnterModal}
        onOk={() => { resetEnterModal(); handleDataUpdate(); }}
        prisonerNo={activePrisonerNo}
        policeFaceImage={policeFaceImage}
        policeFaceName={policeFaceName}
        capturedFaceImage={capturedFaceImage}
        archiveFaceImage={archiveFaceImage}
        onStepChange={handleEnterModalStepChange}
      />
      <ReturnConfirmModal
        visible={returnModalOpen}
        onCancel={() => { setReturnModalOpen(false); setCapturedFaceImage(null); setArchiveFaceImage(null); }}
        onOk={() => { setReturnModalOpen(false); setCapturedFaceImage(null); setArchiveFaceImage(null); handleDataUpdate(); }}
        prisonerNo={activePrisonerNo}
        capturedFaceImage={capturedFaceImage}
        archiveFaceImage={archiveFaceImage}
        policeFaceImage={policeFaceImage}
        policeFaceName={policeFaceName}
      />
      <HandheldSyncModal
        visible={handheldSyncOpen}
        onCancel={() => setHandheldSyncOpen(false)}
      />
    </div>
  );
};

export default Dashboard;