import React, { useState } from 'react';
import { Modal, Steps, Button, Form, Input, Select, DatePicker, message, ConfigProvider, theme } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import { entryRecord } from '@/api/globApi';
import './ExitConfirmModal.less';

const EnterConfirmModal = ({ open, onCancel, onOk }) => {
  const [form] = Form.useForm();
  const [current, setCurrent] = useState(0);
  const [policeImage, setPoliceImage] = useState(null);

  const entryStatus = Form.useWatch('entryStatus', form);

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

  const handleSubmit = async () => {
    const values = form.getFieldsValue();
    try {
      const formData = new FormData();
      formData.append('prisoner_no', values.prisonerNo);
      formData.append('prisoner_name', values.prisonerName);
      formData.append('prison_area', values.prisonArea);
      formData.append('entry_date', values.enterDate ? values.enterDate.format('YYYY-MM-DD') : null);
      formData.append('police_face', policeImage);
      formData.append('entry_status', values.entryStatus || 'normal');
      formData.append('abnormal_reason', values.abnormalReason || '');

      const res = await entryRecord.submit(formData);
      if (res.code === 1) {
        message.success('提交成功');
        onOk?.(values);
        handleReset();
      } else {
        message.error(res.msg || '提交失败');
      }
    } catch (error) {
      message.error('提交失败');
    }
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
          label="监区"
          rules={[{ required: true, message: '请选择监区' }]}
        >
          <Select placeholder="请选择监区" options={[
            { value: '一监区', label: '一监区' },
            { value: '二监区', label: '二监区' },
            { value: '三监区', label: '三监区' },
            { value: '四监区', label: '四监区' },
            { value: '五监区', label: '五监区' },
            { value: '六监区', label: '六监区' },
            { value: '七监区', label: '七监区' },
          ]} />
        </Form.Item>

        <Form.Item
          name="entryStatus"
          label="状态"
          rules={[{ required: true, message: '请选择状态' }]}
        >
          <Select placeholder="请选择状态" options={[
            { value: 'normal', label: '正常' },
            { value: 'abnormal', label: '异常' },
          ]} />
        </Form.Item>

        {entryStatus === 'abnormal' && (
          <Form.Item
            name="abnormalReason"
            label="异常原因"
            rules={[{ required: true, message: '请输入异常原因' }]}
          >
            <Input.TextArea placeholder="请输入异常原因" rows={3} />
          </Form.Item>
        )}
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