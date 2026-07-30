import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Modal, Button, message, Spin, Empty } from 'antd';
import {
  SyncOutlined,
  CheckCircleFilled,
  CloseCircleFilled,
  ClockCircleOutlined,
  SendOutlined,
  DatabaseOutlined,
  WifiOutlined,
  AlertOutlined,
} from '@ant-design/icons';
import { deviceSync } from '@/api/globApi';
import './HandheldSyncModal.less';

const POLL_INTERVAL = 1000;

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
      return data;
    } catch (e) {
      if (!silent) {
        message.error('获取进度失败');
      }
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
    return () => {
      mountedRef.current = false;
    };
  }, [visible, fetchProgress]);

  // 只在同步运行中时启动轮询，空闲时不调用接口
  useEffect(() => {
    if (!visible || !progress?.is_running) {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      return;
    }
    timerRef.current = setInterval(() => fetchProgress(true), POLL_INTERVAL);
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [visible, progress?.is_running, fetchProgress]);

  useEffect(() => {
    if (!progress) return;
    if (progress.is_running) {
      setWasRunning(true);
    }
  }, [progress]);

  const handleStart = async () => {
    const onlineDevices = (progress?.devices || []).filter(d => d.is_online);
    if (onlineDevices.length === 0) {
      message.warning('没有在线设备，请先连接一体机');
      return;
    }
    if (progress?.is_running) {
      message.info('同步进行中，请等待');
      return;
    }
    setStarting(true);
    try {
      const res = await deviceSync.trigger({ full: true });
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

  const handleClose = () => {
    if (progress?.is_running) {
      Modal.confirm({
        title: '同步仍在进行中',
        content: '关闭窗口不会停止同步，但您将看不到进度。确定关闭？',
        okText: '关闭',
        cancelText: '继续查看',
        onOk: () => onCancel?.(),
      });
      return;
    }
    onCancel?.();
  };

  const isRunning = !!progress?.is_running;
  const total = progress?.total || 0;
  const sent = progress?.sent || 0;
  const success = progress?.success || 0;
  const fail = progress?.fail || 0;
  const pending = progress?.pending || 0;
  const error = progress?.error || 0;
  const devices = progress?.devices || [];
  const onlineDevices = devices.filter(d => d.is_online);
  const percent = total > 0 ? Math.min(100, Math.round((sent / total) * 100)) : 0;
  const finishedSuccess = !isRunning && wasRunning && total > 0 && sent > 0;

  const stats = [
    { label: '总数', value: total, icon: <DatabaseOutlined />, color: '#00f0ff' },
    { label: '已发送', value: sent, icon: <SendOutlined />, color: '#1877ff' },
    { label: '成功', value: success, icon: <CheckCircleFilled />, color: '#52c41a' },
    { label: '失败', value: fail + error, icon: <CloseCircleFilled />, color: '#ff4d4f' },
  ];

  return (
    <Modal
      title="同步罪犯到手持终端"
      visible={visible}
      onCancel={handleClose}
      destroyOnClose
      width={680}
      destroyOnClose
      className="handheld-sync-modal"
      maskClosable={!isRunning}
      closable={!isRunning}
      footer={[
        <Button key="close" onClick={handleClose}>关闭</Button>,
        <Button
          key="start"
          type="primary"
          icon={<SyncOutlined spin={isRunning} />}
          onClick={handleStart}
          loading={starting}
          disabled={isRunning || onlineDevices.length === 0}
        >
          {isRunning ? '同步中...' : (wasRunning ? '重新同步' : '开始同步')}
        </Button>,
      ]}
    >
      <div className="sync-body">
        <div className="device-section">
          <div className="section-title">
            <WifiOutlined />
            <span>设备状态</span>
          </div>
          {devices.length === 0 ? (
            <Empty description="暂无设备记录" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ) : (
            <div className="device-list">
              {devices.map(d => (
                <div key={d.device_no} className={`device-card ${d.is_online ? 'online' : 'offline'}`}>
                  <div className="device-status-dot" />
                  <div className="device-info">
                    <div className="device-no">{d.device_no}</div>
                    <div className="device-name">{d.name || '未命名设备'}</div>
                  </div>
                  <div className="device-state">
                    {d.is_online ? '在线' : '离线'}
                  </div>
                </div>
              ))}
            </div>
          )}
          {onlineDevices.length === 0 && (
            <div className="warn-tip">
              <AlertOutlined />
              <span>没有在线设备，无法同步。请先确保一体机已连接并完成声明。</span>
            </div>
          )}
        </div>

        <div className="stats-grid">
          {stats.map(s => (
            <div key={s.label} className="stat-card" style={{ '--accent': s.color }}>
              <div className="stat-icon">{s.icon}</div>
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="progress-section">
          <div className="progress-header">
            <span className="progress-title">下发进度</span>
            <span className="progress-percent">{percent}%</span>
          </div>
          <div className="progress-bar">
            <div
              className={`progress-fill ${isRunning ? 'running' : ''}`}
              style={{ width: `${percent}%` }}
            />
          </div>
          <div className="progress-meta">
            <span>已发送 {sent} / {total}</span>
            <span>等待回执 {pending}</span>
          </div>
        </div>

        <div className="status-line">
          {isRunning ? (
            <>
              <SyncOutlined spin />
              <span className="status-text">{progress?.message || '同步中...'}</span>
            </>
          ) : finishedSuccess ? (
            <>
              <CheckCircleFilled style={{ color: '#52c41a' }} />
              <span className="status-text">同步完成：成功 {success} 条，失败 {fail + error} 条，等待回执 {pending} 条</span>
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

        {isRunning && progress?.current_prisoner_no && (
          <div className="current-item">
            <span className="label">正在下发：</span>
            <span className="name">{progress.current_prisoner_name || '-'}</span>
            <span className="no">({progress.current_prisoner_no})</span>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default HandheldSyncModal;
