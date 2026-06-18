import React from 'react';
import { Modal, ConfigProvider, theme } from 'antd';
import { LogoutOutlined, LoginOutlined, UserOutlined } from '@ant-design/icons';
import './OperationSelectModal.less';

const OperationSelectModal = ({ open, onSelect, prisonerNo, prisonerName }) => {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#00f0ff',
          colorBgElevated: 'rgba(20, 25, 45, 0.98)',
          colorBgContainer: 'rgba(10, 15, 30, 0.98)',
          colorBorder: 'rgba(0, 240, 255, 0.3)',
          colorText: '#fff',
          borderRadius: 8,
        },
      }}
    >
      <Modal
        open={open}
        footer={null}
        width={520}
        closable={false}
        destroyOnClose
        className="operation-select-modal"
        onCancel={() => onSelect?.(null)}
      >
        <div className="op-select-header">
          <div className="op-select-icon">
            <UserOutlined />
          </div>
          <div className="op-select-title">请选择操作类型</div>
          <div className="op-select-info">
            罪犯编号：<span>{prisonerNo || '--'}</span>
            {prisonerName && <><span className="op-info-sep">|</span>姓名：<span>{prisonerName}</span></>}
          </div>
        </div>

        <div className="op-select-cards">
          <div className="op-card op-card-exit" onClick={() => onSelect?.('exit')}>
            <div className="op-card-icon">
              <LogoutOutlined />
            </div>
            <div className="op-card-label">出监确认</div>
            <div className="op-card-desc">罪犯出监流程确认</div>
          </div>

          <div className="op-card op-card-enter" onClick={() => onSelect?.('enter')}>
            <div className="op-card-icon">
              <LoginOutlined />
            </div>
            <div className="op-card-label">入监确认</div>
            <div className="op-card-desc">罪犯入监流程确认</div>
          </div>
        </div>

        <div className="op-select-footer">
          点击卡片选择操作，或点击空白区域取消
        </div>
      </Modal>
    </ConfigProvider>
  );
};

export default OperationSelectModal;
