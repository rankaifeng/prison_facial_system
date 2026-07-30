import React, { useState, useEffect, useRef } from 'react';
import { Modal, Steps, Button, Form, Input, Select, DatePicker, message, Spin, Row, Col } from 'antd';
import { UserOutlined, SafetyOutlined, TeamOutlined, CameraOutlined } from '@ant-design/icons';
import moment from 'moment';
import 'moment/locale/zh-cn';
import SignatureCanvas from './SignatureCanvas';
import { exitRecord, exitType, archive, snapshot } from '@/api/globApi';
import './ExitConfirmModal.less';

moment.locale('zh-cn');

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

const PRISON_AREAS = [
  { value: '1', label: '一监区' },
  { value: '2', label: '二监区' },
  { value: '3', label: '三监区' },
  { value: '4', label: '四监区' },
  { value: '5', label: '五监区' },
  { value: '6', label: '六监区' },
  { value: '7', label: '七监区' },
];

const PRISON_AREA_NAME_TO_ID = {
  '一监区': '1', '二监区': '2', '三监区': '3', '四监区': '4',
  '五监区': '5', '六监区': '6', '七监区': '7',
};

const ExitConfirmModal = ({ visible, onCancel, onOk, prisonerNo, policeFaceImage, swatFaceImage, policeFaceName, swatFaceName, capturedFaceImage, archiveFaceImage, onStepChange }) => {
  const [form] = Form.useForm();
  const [current, setCurrent] = useState(0);
  const [policeImage, setPoliceImage] = useState(null);
  const [swatImage, setSwatImage] = useState(null);
  const [policeName, setPoliceName] = useState(null);
  const [swatName, setSwatName] = useState(null);
  const [armedPoliceSignature, setArmedPoliceSignature] = useState(null);
  const [armedPoliceImage, setArmedPoliceImage] = useState(null);
  const [captureLoading, setCaptureLoading] = useState(false);
  const [exitReasons, setExitReasons] = useState([]);
  const [formValues, setFormValues] = useState({});
  const [startTime, setStartTime] = useState(null);
  const [loadingPrisoner, setLoadingPrisoner] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const policeInputRef = useRef(null);
  const swatInputRef = useRef(null);

  const exitReason = Form.useWatch('exitReason', form);
  const hospitalType = Form.useWatch('hospital', form);
  const centerPrison = Form.useWatch('transferPrison', form);
  const exitReasonName = exitReasons.find(r => r.value === exitReason)?.label;

  useEffect(() => {
    if (visible) {
      setFormValues({});
      form.resetFields();
      setCurrent(0);
      setPoliceImage(null);
      setSwatImage(null);
      setPoliceName(null);
      setSwatName(null);
      setArmedPoliceSignature(null);
      setArmedPoliceImage(null);

      // 通知父组件重置图片状态
      onStepChange?.(0);

      // 获取出监原因列表
      const fetchExitTypes = async () => {
        try {
          const res = await exitType.list();
          if (res && Array.isArray(res)) {
            setExitReasons(res.map(item => ({ value: item.id, label: item.type_name })));
          }
        } catch (error) {
        }
      };
      fetchExitTypes();

      // 根据编号查询罪犯信息并回显
      if (prisonerNo) {
        setLoadingPrisoner(true);
        archive.detail({ prisoner_no: prisonerNo }).then(res => {
          if (res?.code === 1 && res?.data) {
            const d = res.data;
            form.setFieldsValue({
              prisonerNo: d.bh || prisonerNo,
              prisonerName: d.xm || '',
              prisonArea: PRISON_AREA_NAME_TO_ID[d.db] || d.db || '',
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
  }, [visible, prisonerNo, form, onStepChange]);

  // 通知父组件当前步骤
  useEffect(() => {
    onStepChange?.(current);
  }, [current, onStepChange]);

  // 自动填充民警/特警人脸图片和姓名
  useEffect(() => {
    if (policeFaceImage) {
      setPoliceImage(policeFaceImage);
    }
  }, [policeFaceImage]);

  useEffect(() => {
    if (swatFaceImage) {
      setSwatImage(swatFaceImage);
    }
  }, [swatFaceImage]);

  useEffect(() => {
    if (policeFaceName) {
      setPoliceName(policeFaceName);
    }
  }, [policeFaceName]);

  useEffect(() => {
    if (swatFaceName) {
      setSwatName(swatFaceName);
    }
  }, [swatFaceName]);

  const handleNext = async () => {
    if (current === 0) {
      try {
        const values = await form.validateFields();
        setFormValues(values);
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
    } else if (current === 1) {
      setCurrent(2);
    } else if (current === 2) {
      setCurrent(3);
    } else {
      if (!armedPoliceImage) {
        message.warning('请先拍照');
        return;
      }
      if (!armedPoliceSignature) {
        message.warning('请先签字确认');
        return;
      }
      handleSubmit();
    }
  };

  const handleBack = () => {
    setCurrent(current - 1);
  };

  const handleSubmit = async () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() + 2);
    const end = now.getFullYear().toString().padStart(4, '0') +
      (now.getMonth() + 1).toString().padStart(2, '0') +
      now.getDate().toString().padStart(2, '0') + 'T' +
      now.getHours().toString().padStart(2, '0') +
      now.getMinutes().toString().padStart(2, '0') +
      now.getSeconds().toString().padStart(2, '0');

    let hospitalName = null;
    const reasonName = exitReasons.find(r => r.value === formValues.exitReason)?.label;
    if (reasonName === '外出就医') {
      const ht = formValues.hospital;
      if (ht === '中心医院') {
        hospitalName = formValues.transferPrison === '其他' ? formValues.transferPrisonOther : formValues.transferPrison;
      } else if (ht === '社会医院') {
        hospitalName = formValues.socialHospital === '其他' ? formValues.socialHospitalOther : formValues.socialHospital;
      }
    }

    const formData = new FormData();
    formData.append('prisoner_no', formValues.prisonerNo);
    formData.append('prisoner_name', formValues.prisonerName);
    formData.append('prison_area', formValues.prisonArea);
    formData.append('exit_date', formValues.exitDate ? formValues.exitDate.format('YYYY-MM-DD HH:mm') : null);
    formData.append('reason', formValues.exitReason);
    formData.append('police_face', policeImage);
    formData.append('swat_face', swatImage);
    formData.append('police_name', policeName || '');
    formData.append('swat_name', swatName || '');
    formData.append('armed_police_signature', armedPoliceSignature);
    formData.append('armed_police_face', armedPoliceImage || '');
    formData.append('hospital_name', hospitalName || '');
    formData.append('start_time', startTime);
    formData.append('end_time', end);

    if (submitting) return;
    setSubmitting(true);
    try {
      const res = await exitRecord.submit(formData);
      if (res.code === 1) {
        message.success('提交成功');
        onOk?.(formValues);
        handleReset();
      } else {
        message.error(res.msg || '提交失败');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setFormValues({});
    form.resetFields();
    setCurrent(0);
    setPoliceImage(null);
    setSwatImage(null);
    setArmedPoliceSignature(null);
    setArmedPoliceImage(null);
    setStartTime(null);
    onCancel?.();
  };

  const renderStep1 = () => (
    <div className="step-content step-form" style={{ display: current === 0 ? 'flex' : 'none' }}>
      {/* 双图片展示区 */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 40, marginBottom: 20 }}>
        <div style={{ textAlign: 'center' }}>
          <div className="confirm-image" style={{ width: 140, height: 140 }}>
            {capturedFaceImage ? (
              <img src={capturedFaceImage} alt="终端抓拍" />
            ) : (
              <div className="image-placeholder"><UserOutlined /><span>无抓拍</span></div>
            )}
          </div>
          <div style={{ marginTop: 8, fontSize: 13, color: 'rgba(255,255,255,0.7)' }}>终端抓拍</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div className="confirm-image" style={{ width: 140, height: 140 }}>
            {archiveFaceImage ? (
              <img src={archiveFaceImage} alt="档案照片" />
            ) : (
              <div className="image-placeholder"><UserOutlined /><span>无档案</span></div>
            )}
          </div>
          <div style={{ marginTop: 8, fontSize: 13, color: 'rgba(255,255,255,0.7)' }}>档案照片</div>
        </div>
      </div>
      {loadingPrisoner ? (
        <div style={{ textAlign: 'center', padding: 40, width: '100%' }}>
          <Spin tip="正在查询罪犯信息..." />
        </div>
      ) : (
        <Form form={form} layout="vertical" initialValues={{ exitDate: moment() }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="prisonerNo" label="罪犯编号" rules={[{ required: true, message: '请输入罪犯编号' }]}>
                <Input placeholder="请输入罪犯编号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="prisonerName" label="罪犯姓名" rules={[{ required: true, message: '请输入罪犯姓名' }]}>
                <Input placeholder="请输入罪犯姓名" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="prisonArea" label="监区" rules={[{ required: true, message: '请输入监区' }]}>
                <Input placeholder="请输入监区" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="exitDate" label="出监日期" rules={[{ required: true, message: '请选择出监日期' }]}>
                <DatePicker style={{ width: '100%' }} placeholder="请选择出监日期" showTime format="YYYY-MM-DD HH:mm" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="exitReason" label="出监原因" rules={[{ required: true, message: '请选择出监原因' }]}>
                <Select placeholder="请选择出监原因" options={exitReasons} />
              </Form.Item>
            </Col>
            {exitReasonName === '外出就医' && (
              <Col span={12}>
                <Form.Item name="hospital" label="医院类型" rules={[{ required: true, message: '请选择医院类型' }]}>
                  <Select placeholder="请选择医院类型" options={HOSPITALS_CENTER} />
                </Form.Item>
              </Col>
            )}
          </Row>
          {exitReasonName === '外出就医' && hospitalType === '中心医院' && (
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="transferPrison" label="转诊监狱" rules={[{ required: true, message: '请选择转诊监狱' }]}>
                  <Select placeholder="请选择转诊监狱" options={CENTER_PRISONS} />
                </Form.Item>
              </Col>
              {centerPrison === '其他' && (
                <Col span={12}>
                  <Form.Item name="transferPrisonOther" label="转诊监狱（其他）" rules={[{ required: true, message: '请输入转诊监狱' }]}>
                    <Input placeholder="请输入转诊监狱" />
                  </Form.Item>
                </Col>
              )}
            </Row>
          )}
          {exitReasonName === '外出就医' && hospitalType === '社会医院' && (
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="socialHospital" label="医院" rules={[{ required: true, message: '请选择医院' }]}>
                  <Select placeholder="请选择医院" options={SOCIAL_HOSPITALS} />
                </Form.Item>
              </Col>
              {form.getFieldValue('socialHospital') === '其他' && (
                <Col span={12}>
                  <Form.Item name="socialHospitalOther" label="医院（其他）" rules={[{ required: true, message: '请输入医院名称' }]}>
                    <Input placeholder="请输入医院名称" />
                  </Form.Item>
                </Col>
              )}
            </Row>
          )}
        </Form>
      )}
    </div>
  );

  const renderStep2 = () => (
    <div className="step-content confirm-step" style={{ display: current === 1 ? 'flex' : 'none' }}>
      <input type="file" ref={policeInputRef} accept="image/*" style={{ display: 'none' }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = (ev) => setPoliceImage(ev.target.result);
            reader.readAsDataURL(file);
          }
        }}
      />
      <div style={{ textAlign: 'center' }}>
        <div className="confirm-image">
          {policeImage ? (
            <img src={policeImage} alt="民警照片" />
          ) : (
            <div className="image-placeholder"><UserOutlined /><span>等待录入</span></div>
          )}
        </div>
        {policeName && <div style={{ marginTop: 12, fontSize: 16, color: '#fff', fontWeight: 600 }}>{policeName}</div>}
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="step-content confirm-step" style={{ display: current === 2 ? 'flex' : 'none' }}>
      <input type="file" ref={swatInputRef} accept="image/*" style={{ display: 'none' }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = (ev) => setSwatImage(ev.target.result);
            reader.readAsDataURL(file);
          }
        }}
      />
      <div style={{ textAlign: 'center' }}>
        <div className="confirm-image">
          {swatImage ? (
            <img src={swatImage} alt="特警照片" />
          ) : (
            <div className="image-placeholder"><UserOutlined /><span>等待录入</span></div>
          )}
        </div>
        {swatName && <div style={{ marginTop: 12, fontSize: 16, color: '#fff', fontWeight: 600 }}>{swatName}</div>}
      </div>
    </div>
  );

  const handleCapture = async () => {
    setCaptureLoading(true);
    try {
      const res = await snapshot.capture({ channel: 1 });
      if (res?.code === 1 && res?.data?.image_base64) {
        setArmedPoliceImage('data:image/jpeg;base64,' + res.data.image_base64);
        message.success('拍照成功');
      } else {
        message.error(res?.msg || '拍照失败');
      }
    } catch (e) {
      message.error('拍照请求失败');
    } finally {
      setCaptureLoading(false);
    }
  };

  const renderStep4 = () => (
    <div className="step-content confirm-step" style={{ display: current === 3 ? 'flex' : 'none', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
      <div style={{ display: 'flex', gap: 24, width: '100%', justifyContent: 'center', alignItems: 'flex-start' }}>
        <div style={{ textAlign: 'center', flex: 1, maxWidth: 260 }}>
          <div style={{ marginBottom: 8, color: '#fff', fontSize: 14 }}>武警人脸</div>
          <div className="confirm-image" style={{ width: '100%', height: 220 }}>
            {armedPoliceImage ? (
              <img src={armedPoliceImage} alt="武警照片" />
            ) : (
              <div className="image-placeholder"><UserOutlined /><span>未拍照</span></div>
            )}
          </div>
          <Button
            icon={<CameraOutlined />}
            loading={captureLoading}
            onClick={handleCapture}
            style={{ marginTop: 16 }}
            type="primary"
          >
            拍照
          </Button>
        </div>
        <div style={{ textAlign: 'center', flex: 1, maxWidth: 320, marginLeft: 10 }}>
          <div style={{ marginBottom: 8, color: '#fff', fontSize: 14 }}>武警签字</div>
          <div className="signature-wrapper">
            {armedPoliceSignature ? (
              <img src={armedPoliceSignature} alt="签字" className="signature-preview" />
            ) : (
              <SignatureCanvas onSave={(data) => setArmedPoliceSignature(data)} onClear={() => setArmedPoliceSignature(null)} />
            )}
          </div>
        </div>
      </div>
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
      visible={visible}
      onCancel={handleReset}
      width={680}
      destroyOnClose
      className="exit-confirm-modal"
      footer={[
        <Button key="cancel" onClick={handleReset}>取消</Button>,
        current > 0 && <Button key="back" onClick={handleBack}>上一步</Button>,
        <Button key="next" type="primary" onClick={handleNext} loading={current === 3 && submitting}>
          {current === 3 ? '确认提交' : '下一步'}
        </Button>,
      ].filter(Boolean)}
    >
      <Steps current={current} className="exit-steps">
        {steps.map(step => <Steps.Step key={step.title} title={step.title} icon={step.icon} />)}
      </Steps>
      {current === 0 && renderStep1()}
      {current === 1 && renderStep2()}
      {current === 2 && renderStep3()}
      {current === 3 && renderStep4()}
    </Modal>
  );
};

export default ExitConfirmModal;
