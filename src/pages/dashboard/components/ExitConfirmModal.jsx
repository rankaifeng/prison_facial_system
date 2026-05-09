import React, { useState } from 'react';
import { Modal, Steps, Button, Form, Input, Select, DatePicker, Space, message } from 'antd';
import { UserOutlined, SafetyOutlined, TeamOutlined, EditOutlined } from '@ant-design/icons';
import './ExitConfirmModal.less';

const { RangePicker } = DatePicker;

const PRISONS = ['分监区一', '分监区二', '分监区三', '分监区四', '分监区五', '分监区六', '分监区七'];

const EXIT_REASONS = [
  { value: '刑满释放', label: '刑满释放' },
  { value: '外出就医', label: '外出就医' },
  { value: '外出教育', label: '外出教育' },
  { value: '离监探亲', label: '离监探亲' },
  { value: '押回重审', label: '押回重审' },
];

const HOSPITALS_CENTER = [
  { value: '中心医院', label: '中心医院' },
  { value: '社会医院', label: '社会医院' },
];

const CENTER_PRISONS = [
  { value: '金蓥监狱', label: '金蓥监狱' },
  { value: '成都病犯监狱', label: '成都病犯监狱' },
  { value: '其他', label: '其他' },
];

const SOCIAL_HOSPITALS = [
  { value: '达州市中心医院', label: '达州市中心医院' },
  { value: '达州区人民医院', label: '达州区人民医院' },
  { value: '其他', label: '其他' },
];

const ExitConfirmModal = ({ open, onCancel, onOk }) => {
  const [form] = Form.useForm();
  const [current, setCurrent] = useState(0);
  const [policeImage, setPoliceImage] = useState(null);
  const [swatImage, setSwatImage] = useState(null);
  const [armedPoliceSignature, setArmedPoliceSignature] = useState(null);

  const exitReason = Form.useWatch('exitReason', form);
  const hospitalType = Form.useWatch('hospital', form);
  const centerPrison = Form.useWatch('transferPrison', form);

  const handleNext = async () => {
    if (current === 0) {
      try {
        await form.validateFields();
        setCurrent(1);
      } catch {
        return;
      }
    } else if (current === 1) {
      setPoliceImage('/imgs/face.png');
      setCurrent(2);
    } else if (current === 2) {
      setSwatImage('/imgs/face.png');
      setCurrent(3);
    } else {
      setArmedPoliceSignature('/imgs/face.png');
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
      swatImage,
      armedPoliceSignature,
    };
    message.success('提交成功');
    onOk?.(data);
    handleReset();
  };

  const handleReset = () => {
    form.resetFields();
    setCurrent(0);
    setPoliceImage(null);
    setSwatImage(null);
    setArmedPoliceSignature(null);
    onCancel?.();
  };

  const renderStep1 = () => (
    <div className="step-content">
      <Form
        form={form}
        layout="vertical"
        initialValues={{ exitDate: null }}
      >
        <Form.Item
          name="prisonerName"
          label="罪犯姓名"
          rules={[{ required: true, message: '请输入罪犯姓名' }]}
        >
          <Input placeholder="请输入罪犯姓名" />
        </Form.Item>

        <Form.Item
          name="exitDate"
          label="出监日期"
          rules={[{ required: true, message: '请选择出监日期' }]}
        >
          <DatePicker style={{ width: '100%' }} placeholder="请选择出监日期" />
        </Form.Item>

        <Form.Item
          name="exitReason"
          label="出监原因"
          rules={[{ required: true, message: '请选择出监原因' }]}
        >
          <Select placeholder="请选择出监原因" options={EXIT_REASONS} />
        </Form.Item>

       

        {exitReason === '外出就医' && (
          <Form.Item
            name="hospital"
            label="医院"
            rules={[{ required: true, message: '请选择医院' }]}
          >
            <Select placeholder="请选择医院" options={HOSPITALS_CENTER} />
          </Form.Item>
        )}

        {exitReason === '外出就医' && hospitalType === '中心医院' && (
          <Form.Item
            name="transferPrison"
            label="转诊监狱"
            rules={[{ required: true, message: '请选择转诊监狱' }]}
          >
            <Select placeholder="请选择转诊监狱" options={CENTER_PRISONS} />
          </Form.Item>
        )}

        {exitReason === '外出就医' && hospitalType === '中心医院' && centerPrison === '其他' && (
          <Form.Item
            name="transferPrisonOther"
            label="转诊监狱（其他）"
            rules={[{ required: true, message: '请输入转诊监狱' }]}
          >
            <Input placeholder="请输入转诊监狱" />
          </Form.Item>
        )}

        {exitReason === '外出就医' && hospitalType === '社会医院' && (
          <Form.Item
            name="socialHospital"
            label="医院"
            rules={[{ required: true, message: '请选择医院' }]}
          >
            <Select placeholder="请选择医院" options={SOCIAL_HOSPITALS} />
          </Form.Item>
        )}

        {exitReason === '外出就医' && hospitalType === '社会医院' && form.getFieldValue('socialHospital') === '其他' && (
          <Form.Item
            name="socialHospitalOther"
            label="医院（其他）"
            rules={[{ required: true, message: '请输入医院名称' }]}
          >
            <Input placeholder="请输入医院名称" />
          </Form.Item>
        )}
         <Form.Item
          name="prisonArea"
          label="分监区"
          rules={[{ required: true, message: '请选择分监区' }]}
        >
          <Select placeholder="请选择分监区" options={PRISONS.map(p => ({ value: p, label: p }))} />
        </Form.Item>
      </Form>
    </div>
  );

  const renderStep2 = () => (
    <div className="step-content confirm-step">
      <div className="confirm-image">
        {policeImage ? (
          <img src={policeImage} alt="民警照片" />
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

  const renderStep3 = () => (
    <div className="step-content confirm-step">
      <div className="confirm-image">
        {swatImage ? (
          <img src={swatImage} alt="特警照片" />
        ) : (
          <div className="image-placeholder">
            <SafetyOutlined />
            <span>等待录入</span>
          </div>
        )}
      </div>
      <Button type="primary" onClick={() => setSwatImage('/imgs/face.png')}>
        确认
      </Button>
    </div>
  );

  const renderStep4 = () => (
    <div className="step-content confirm-step">
      <div className="confirm-image signature">
        {armedPoliceSignature ? (
          <img src={armedPoliceSignature} alt="签字" />
        ) : (
          <div className="image-placeholder">
            <EditOutlined />
            <span>等待签字</span>
          </div>
        )}
      </div>
      <Button type="primary" onClick={() => setArmedPoliceSignature('/imgs/face.png')}>
        录入签字
      </Button>
    </div>
  );

  const steps = [
    { title: '基本信息', icon: <UserOutlined /> },
    { title: '民警确认', icon: <UserOutlined /> },
    { title: '特警确认', icon: <SafetyOutlined /> },
    { title: '武警确认', icon: <TeamOutlined /> },
  ];

  return (
    <Modal
      title="出监确认"
      open={open}
      onCancel={handleReset}
      width={600}
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
          {current === 3 ? '确认提交' : '下一步'}
        </Button>,
      ].filter(Boolean)}
    >
      <Steps current={current} items={steps} className="exit-steps" />
      {current === 0 && renderStep1()}
      {current === 1 && renderStep2()}
      {current === 2 && renderStep3()}
      {current === 3 && renderStep4()}
    </Modal>
  );
};

export default ExitConfirmModal;