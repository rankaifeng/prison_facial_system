import React, { useState } from 'react';
import { Modal, Steps, Button, Form, Input, Select, DatePicker, message, ConfigProvider, theme } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import './ExitConfirmModal.less';

const EnterConfirmModal = ({ open, onCancel, onOk }) => {
  const [form] = Form.useForm();
  const [current, setCurrent] = useState(0);
  const [policeImage, setPoliceImage] = useState(null);

  const handleNext = async () => {
    if (current === 0) {
      try {
        await form.validateFields();
        setCurrent(1);
      } catch {
        return;
      }
    } else {
      if (!policeImage) {
        message.warning('请先录入人脸');
        return;
      }
      handleSubmit();
    }
  };

  const handleBack = () => {
    setCurrent(current - 1);
  };

  const handleSubmit = () => {
    const values = form.getFieldsValue();
    const data = {
      ...values,
      policeImage,
    };
    message.success('提交成功');
    onOk?.(data);
    handleReset();
  };

  const handleReset = () => {
    form.resetFields();
    setCurrent(0);
    setPoliceImage(null);
    onCancel?.();
  };

  const renderStep1 = () => (
    <div className="step-content step-form">
      <Form form={form} layout="vertical">
        <Form.Item
          name="prisonerName"
          label="罪犯姓名"
        >
          <Input placeholder="罪犯姓名（自动带出）" disabled />
        </Form.Item>

        <Form.Item
          name="prisonerNo"
          label="罪犯编号"
        >
          <Input placeholder="罪犯编号（自动带出）" disabled />
        </Form.Item>

        <Form.Item
          name="enterDate"
          label="入监日期"
          rules={[{ required: true, message: '请选择入监日期' }]}
        >
          <DatePicker style={{ width: '100%' }} placeholder="请选择入监日期" />
        </Form.Item>

        <Form.Item
          name="prisonArea"
          label="分监区"
          rules={[{ required: true, message: '请选择分监区' }]}
        >
          <Select placeholder="请选择分监区" options={[
            { value: '分监区一', label: '分监区一' },
            { value: '分监区二', label: '分监区二' },
            { value: '分监区三', label: '分监区三' },
            { value: '分监区四', label: '分监区四' },
            { value: '分监区五', label: '分监区五' },
            { value: '分监区六', label: '分监区六' },
            { value: '分监区七', label: '分监区七' },
          ]} />
        </Form.Item>
      </Form>
    </div>
  );

  const renderStep2 = () => (
    <div className="step-content confirm-step">
      <div className="confirm-image">
        {policeImage ? (
          <img src={policeImage} alt="民警人脸" />
        ) : (
          <div className="image-placeholder">
            <UserOutlined />
            <span>等待录入</span>
          </div>
        )}
      </div>
      <Button type="primary" onClick={() => setPoliceImage('/imgs/face.png')}>
        确认
      </Button>
    </div>
  );

  const steps = [
    { title: '基本信息', icon: <UserOutlined /> },
    { title: '民警确认', icon: <UserOutlined /> },
  ];

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
          colorTextPlaceholder: 'rgba(255, 255, 255, 0.5)',
          borderRadius: 8,
        },
      }}
    >
      <Modal
        title="入监确认"
        open={open}
        onCancel={handleReset}
        width={680}
        className="exit-confirm-modal"
        footer={[
          <Button key="cancel" onClick={handleReset}>
            取消
          </Button>,
          current > 0 && (
            <Button key="back" onClick={handleBack}>
              上一步
            </Button>
          ),
          <Button key="next" type="primary" onClick={handleNext}>
            {current === 1 ? '确认提交' : '下一步'}
          </Button>,
        ].filter(Boolean)}
      >
        <Steps current={current} items={steps} className="exit-steps" />
        {current === 0 && renderStep1()}
        {current === 1 && renderStep2()}
      </Modal>
    </ConfigProvider>
  );
};

export default EnterConfirmModal;