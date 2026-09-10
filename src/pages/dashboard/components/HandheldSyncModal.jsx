import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Modal, Button, message } from 'antd';
import {
  SyncOutlined,
  CheckCircleFilled,
  CloseCircleFilled,
  ClockCircleOutlined,
  SendOutlined,
  DatabaseOutlined,
  UserOutlined,
  PictureOutlined,
  ApiOutlined,
} from '@ant-design/icons';
import { deviceSync } from '@/api/globApi';
import './HandheldSyncModal.less';

const POLL_INTERVAL = 1500;

const PHASE_LABELS = {
  persons: '人员注册',
  photos: '照片注册',
  callback: '设置回调',
};

const PHASE_ICONS = {
  persons: <UserOutlined />,
  photos: <PictureOutlined />,
  callback: <ApiOutlined />,
};

const HandheldSyncModal = ({ visible, onCancel }) => {
  const [progress, setProgress] = useState(null);
  const [starting, setStarting] = useState(false);
  const [wasRunning, setWasRunning] = useState(false);
  const timerRef = useRef(null);
  const mountedRef = useRef(true);

  const fetchProgress = useCallback(async (silent = false) => {
    try {
      const data = await deviceSync.progress();
      if (!mountedRef.current) return;
      setProgress(data);
      // 重新打开弹窗时，如果同步已完成/出错，也要标记 wasRunning
      if (data?.phase === 'done' || data?.phase === 'error') {
        setWasRunning(true);
      }
      return data;
    } catch (e) {
      if (!silent) message.error('获取进度失败');
      return null;
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    if (visible) {
      fetchProgress();
    } else {
      setProgress(null);
      setStarting(false);
      setWasRunning(false);
    }
    return () => { mountedRef.current = false; };
  }, [visible, fetchProgress]);

  useEffect(() => {
    if (!visible || !progress?.is_running) {
      if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
      return;
    }
    timerRef.current = setInterval(() => fetchProgress(true), POLL_INTERVAL);
    return () => { if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; } };
  }, [visible, progress?.is_running, fetchProgress]);

  useEffect(() => {
    if (progress?.is_running) setWasRunning(true);
  }, [progress]);

  const handleStart = async () => {
    if (progress?.is_running) { message.info('同步进行中，请等待'); return; }
    setStarting(true);
    try {
      const res = await deviceSync.trigger();
      if (res?.code === 1) {
        message.success('已开始同步');
        setWasRunning(true);
        await fetchProgress();
      } else {
        message.error(res?.msg || '触发同步失败');
      }
    } catch (e) {
      message.error('触发同步失败');
    } finally {
      setStarting(false);
    }
  };

  const [cancelling, setCancelling] = useState(false);

  const handleClose = () => {
    if (progress?.is_running) {
      Modal.confirm({
        title: '停止同步',
        content: '关闭窗口将停止当前同步任务，确定停止？',
        okText: '停止同步',
        cancelText: '继续同步',
        okButtonProps: { loading: cancelling },
        onOk: async () => {
          setCancelling(true);
          try {
            await deviceSync.cancel();
          } catch (e) { /* ignore */ }
          setCancelling(false);
          onCancel?.();
        },
      });
      return;
    }
    onCancel?.();
  };

  const isRunning = !!progress?.is_running;
  const phase = progress?.phase || 'idle';
  const total = progress?.total || 0;
  const completed = progress?.completed || 0;
  const success = progress?.success || 0;
  const fail = progress?.fail || 0;
  const percent = total > 0 ? Math.min(100, Math.round((completed / total) * 100)) : 0;
  const finished = !isRunning && wasRunning && total > 0;

  // 阶段结果
  const personsTotal = progress?.persons_total || 0;
  const personsSuccess = progress?.persons_success || 0;
  const personsFail = progress?.persons_fail || 0;
  const photosTotal = progress?.photos_total || 0;
  const photosSuccess = progress?.photos_success || 0;
  const photosFail = progress?.photos_fail || 0;

  // 是否显示人员注册结果（照片阶段及之后）
  const showPersonsResult = personsTotal > 0 && (phase === 'photos' || phase === 'callback' || phase === 'done' || finished);
  // 是否显示照片注册结果（回调阶段及之后）
  const showPhotosResult = photosTotal > 0 && (phase === 'callback' || phase === 'done' || finished);

  const phaseLabel = PHASE_LABELS[phase] || '';
  const phaseIcon = PHASE_ICONS[phase] || null;

  const stats = [
    { label: '总数', value: total, icon: <DatabaseOutlined />, color: '#00f0ff' },
    { label: '已完成', value: completed, icon: <SendOutlined />, color: '#1877ff' },
    { label: '成功', value: success, icon: <CheckCircleFilled />, color: '#52c41a' },
    { label: '失败', value: fail, icon: <CloseCircleFilled />, color: '#ff4d4f' },
  ];

  return (
    <Modal
      title="同步罪犯到手持终端"
      visible={visible}
      onCancel={handleClose}
      destroyOnClose
      width={580}
      className="handheld-sync-modal"
      maskClosable={false}
      closable={true}
      footer={[
        <Button key="close" onClick={handleClose}>关闭</Button>,
        <Button
          key="start"
          type="primary"
          icon={<SyncOutlined spin={isRunning} />}
          onClick={handleStart}
          loading={starting}
          disabled={isRunning}
        >
          {isRunning ? '同步中...' : (finished ? '重新同步' : '开始同步')}
        </Button>,
      ]}
    >
      <div className="sync-body">
        阶段结果
        {showPersonsResult && (
          <div className="phase-result">
            <UserOutlined className="result-icon" />
            <span className="result-label">人员注册完成：</span>
            <span className="result-value">共 {personsTotal} 人，成功 {personsSuccess}，失败 {personsFail}</span>
          </div>
        )}
        {showPhotosResult && (
          <div className="phase-result">
            <PictureOutlined className="result-icon" />
            <span className="result-label">照片注册完成：</span>
            <span className="result-value">共 {photosTotal} 人，成功 {photosSuccess}，失败 {photosFail}</span>
          </div>
        )}

        {/* 统计卡片 */}
        <div className="stats-grid">
          {stats.map(s => (
            <div key={s.label} className="stat-card" style={{ '--accent': s.color }}>
              <div className="stat-icon">{s.icon}</div>
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>

        {/* 进度条 */}
        <div className="progress-section">
          <div className="progress-header">
            <span className="progress-title">
              {phaseLabel ? `${phaseLabel}进度` : '同步进度'}
            </span>
            <span className="progress-percent">{percent}%</span>
          </div>
          <div className="progress-bar">
            <div
              className={`progress-fill ${isRunning ? 'running' : ''}`}
              style={{ width: `${percent}%` }}
            />
          </div>
          <div className="progress-meta">
            <span>已完成 {completed} / {total}</span>
            {isRunning && phaseLabel && (
              <span className="meta-phase">{phaseIcon} {phaseLabel}中...</span>
            )}
          </div>
        </div>

        {/* 状态行 */}
        <div className="status-line">
          {isRunning ? (
            <>
              <SyncOutlined spin />
              <span className="status-text">{progress?.message || '同步中...'}</span>
            </>
          ) : finished ? (
            <>
              <CheckCircleFilled style={{ color: '#52c41a' }} />
              <span className="status-text">{progress?.message || '同步完成'}</span>
            </>
          ) : (progress?.message && progress.message !== '空闲') ? (
            <>
              <ClockCircleOutlined />
              <span className="status-text">{progress.message}</span>
            </>
          ) : (
            <>
              <ClockCircleOutlined />
              <span className="status-text">点击"开始同步"下发档案库所有罪犯到手持终端</span>
            </>
          )}
        </div>

        {/* 当前处理 */}
        {isRunning && progress?.current_name && (
          <div className="current-item">
            <span className="label">正在处理：</span>
            <span className="name">{progress.current_name}</span>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default HandheldSyncModal;
