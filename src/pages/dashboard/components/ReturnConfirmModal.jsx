import React, { useState, useEffect, useRef } from 'react';
import { Modal, Steps, Button, Form, Input, Select, DatePicker, message, Spin } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import moment from 'moment';
import 'moment/locale/zh-cn';
import { returnRecord, archive } from '@/api/globApi';
import './ExitConfirmModal.less';

moment.locale('zh-cn');

const ReturnConfirmModal = ({ visible, onCancel, onOk, prisonerNo }) => {
  const [form] = Form.useForm();
  const [current, setCurrent] = useState(0);
  const [policeImage, setPoliceImage] = useState(null);
  const [formValues, setFormValues] = useState({});
  const [startTime, setStartTime] = useState(null);
  const [loadingPrisoner, setLoadingPrisoner] = useState(false);
  const policeInputRef = useRef(null);

  // 当弹窗打开时重置状态
  useEffect(() => {
    if (visible) {
      form.resetFields();
      setCurrent(0);
      setPoliceImage(null);
      setFormValues({});
      setStartTime(null);

      // 根据编号查询罪犯信息并回显
      if (prisonerNo) {
        setLoadingPrisoner(true);
        archive.detail({ prisoner_no: prisonerNo }).then(res => {
          if (res?.code === 1 && res?.data) {
            const d = res.data;
            form.setFieldsValue({
              prisonerNo: d.bh || prisonerNo,
              prisonerName: d.xm || '',
              prisonArea: d.db || '',
            });
          } else {
            message.error(res?.msg || '未找到该罪犯');
          }
        }).catch(() => {
          message.error('查询罪犯信息失败');
        }).finally(() => {
          setLoadingPrisoner(false);
        });
      }
    }
  }, [visible, prisonerNo, form]);

  const entryStatus = Form.useWatch('entryStatus', form);

  const handleNext = async () => {
    if (current === 0) {
      try {
        const values = await form.validateFields();
        setFormValues(values);
        // 开始时间 = 当前时间往前推2分钟，格式：YYYYMMDDTHHmmss
        const now = new Date();
        now.setMinutes(now.getMinutes() - 2);
        const start = now.getFullYear().toString().padStart(4, '0') +
          (now.getMonth() + 1).toString().padStart(2, '0') +
          now.getDate().toString().padStart(2, '0') + 'T' +
          now.getHours().toString().padStart(2, '0') +
          now.getMinutes().toString().padStart(2, '0') +
          now.getSeconds().toString().padStart(2, '0');
        setStartTime(start);
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
    // 结束时间 = 当前时间往后推2分钟，格式：YYYYMMDDTHHmmss
    const now = new Date();
    now.setMinutes(now.getMinutes() + 2);
    const end = now.getFullYear().toString().padStart(4, '0') +
      (now.getMonth() + 1).toString().padStart(2, '0') +
      now.getDate().toString().padStart(2, '0') + 'T' +
      now.getHours().toString().padStart(2, '0') +
      now.getMinutes().toString().padStart(2, '0') +
      now.getSeconds().toString().padStart(2, '0');

    try {
      const formData = new FormData();
      formData.append('prisoner_no', formValues.prisonerNo);
      formData.append('prisoner_name', formValues.prisonerName);
      formData.append('prison_area', formValues.prisonArea);
      formData.append('entry_date', formValues.returnDate ? formValues.returnDate.format('YYYY-MM-DD HH:mm') : null);
      formData.append('police_face', policeImage);
      formData.append('entry_status', formValues.entryStatus || 'normal');
      formData.append('abnormal_reason', formValues.abnormalReason || '');
      formData.append('start_time', startTime);
      formData.append('end_time', end);

      const res = await returnRecord.submit(formData);
      if (res.code === 1) {
        message.success('提交成功');
        onOk?.(formValues);
        handleReset();
      } else {
        message.error(res.msg || '提交失败');
      }
    } catch (error) {
      message.error('提交失败');
    }
  };

  const handleReset = () => {
    setCurrent(0);
    setPoliceImage(null);
    setFormValues({});
    setStartTime(null);
    onCancel?.();
  };

  const renderStep1 = () => (
    <div className="step-content step-form">
      {loadingPrisoner ? (
        <div style={{ textAlign: 'center', padding: 40, width: '100%' }}>
          <Spin tip="正在查询罪犯信息..." />
        </div>
      ) : (
        <Form form={form} layout="vertical" initialValues={{ returnDate: moment() }}>
          <Form.Item
            name="prisonerNo"
            label="罪犯编号"
            rules={[{ required: true, message: '请输入罪犯编号' }]}
          >
            <Input placeholder="请输入罪犯编号" />
          </Form.Item>

          <Form.Item
            name="prisonerName"
            label="罪犯姓名"
            rules={[{ required: true, message: '请输入罪犯姓名' }]}
          >
            <Input placeholder="请输入罪犯姓名" />
          </Form.Item>
          <Form.Item
            name="prisonArea"
            label="监区"
            rules={[{ required: true, message: '请输入监区' }]}
          >
            <Input placeholder="请输入监区" />
          </Form.Item>
          <Form.Item
            name="returnDate"
            label="回监日期"
            rules={[{ required: true, message: '请选择回监日期' }]}
          >
            <DatePicker showTime format="YYYY-MM-DD HH:mm" style={{ width: '100%' }} placeholder="请选择回监日期" />
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
      )}
    </div>
  );

  const renderStep2 = () => (
    <div className="step-content confirm-step">
      <input
        type="file"
        ref={policeInputRef}
        accept="image/*"
        style={{ display: 'none' }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = (ev) => setPoliceImage(ev.target.result);
            reader.readAsDataURL(file);
          }
        }}
      />
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
    </div>
  );

  const steps = [
    { title: '基本信息', icon: <UserOutlined /> },
    { title: '民警确认', icon: <UserOutlined /> },
  ];

  return (
    <Modal
      title="回监确认"
      visible={visible}
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
      <Steps current={current} className="exit-steps">
        {steps.map(step => <Steps.Step key={step.title} title={step.title} icon={step.icon} />)}
      </Steps>
      {current === 0 && renderStep1()}
      {current === 1 && renderStep2()}
    </Modal>
  );
};

export default ReturnConfirmModal;