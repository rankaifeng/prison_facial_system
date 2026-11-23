import React, { useEffect, useState } from 'react';
import { Alert, Button, Form, Image, Input, message, Modal, Select, Space, Spin, Table, Tabs, Tag } from 'antd';
import http from '@/server/axios';

const RELEASE_CHECK_URL = '/user_manage/archive/release-check';
const decisions = {
  verified: { label: '身份已核对', color: 'success' },
  needs_review: { label: '待复核', color: 'warning' },
};

const Photo = ({ url }) => {
  const [failed, setFailed] = useState(false);
  if (!url) return '无照片';
  if (failed) return <Tag color="warning">照片无法加载</Tag>;
  return (
    <Image
      src={url.startsWith('/media/') ? `/api${url}` : url}
      width={60}
      alt="档案照片"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
    />
  );
};

const identityColumns = [
  { title: '姓名', dataIndex: 'prisoner_name', width: 110 },
  { title: '罪犯编号', dataIndex: 'prisoner_no', width: 130 },
  { title: '档案照片', dataIndex: 'photo_url', width: 120, render: url => <Photo key={url} url={url} /> },
];

const columns = [
  ...identityColumns,
  { title: '监区', dataIndex: 'prison_area', width: 90 },
  { title: '原判刑期', dataIndex: 'sentence', width: 110 },
  { title: '刑期起日', dataIndex: 'sentence_start', width: 120 },
  { title: '预计释放日期', dataIndex: 'release_date', width: 125, render: value => value || '—' },
  {
    title: '刑期止日',
    dataIndex: 'sentence_end',
    width: 150,
    render: (value, row) => (
      <>
        {value || '—'}
        {row.raw_sentence_end && <div>原始档案 {row.raw_sentence_end}</div>}
      </>
    ),
  },
  {
    title: '资料提醒',
    dataIndex: 'issues',
    width: 230,
    render: issues => issues.length
      ? <ul style={{ margin: 0, paddingLeft: 18 }}>{issues.map(issue => <li key={issue}>{issue}</li>)}</ul>
      : <Tag color="green">字段检查无异常</Tag>,
  },
];

const ReleaseCheck = ({ onClose }) => {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(false);
  const [reviewing, setReviewing] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [form] = Form.useForm();

  useEffect(() => {
    let active = true;
    http.get(RELEASE_CHECK_URL).then(result => {
      if (result.code !== 1 || !result.data) throw new Error('自检请求失败');
      if (active) setReport(result.data);
    }).catch(() => {
      if (active) setError(true);
    });
    return () => { active = false; };
  }, []);

  const openReview = row => {
    setSaveError('');
    setReviewing(row);
    form.setFieldsValue({ decision: row.review?.decision, note: row.review?.note || '' });
  };

  const saveReview = async values => {
    setSaving(true);
    setSaveError('');
    try {
      const result = await http.post(RELEASE_CHECK_URL, {
        archive_id: reviewing.id,
        release_date: reviewing.release_date,
        decision: values.decision,
        note: values.note || '',
      });
      if (result.code !== 1 || !result.data) {
        setSaveError(result.msg || '保存失败，请重试。');
        return;
      }
      setReport(current => ({
        ...current,
        rows: current.rows.map(row => row.id === reviewing.id ? { ...row, review: result.data } : row),
      }));
      setReviewing(null);
      message.success('核对结果已保存');
    } catch {
      setSaveError('保存失败，请重试。');
    } finally {
      setSaving(false);
    }
  };

  const reviewColumn = {
    title: '人工核对',
    key: 'review',
    width: 230,
    render: (_, row) => {
      const review = row.review;
      const decision = decisions[review?.decision];
      return (
        <Space direction="vertical" size={4}>
          <Tag color={decision?.color}>{decision?.label || '待人工核对'}</Tag>
          {review && <>
            <span>{review.reviewer} · {review.reviewed_at.slice(0, 16).replace('T', ' ')}</span>
            {review.note && <span style={{ overflowWrap: 'anywhere' }}>{review.note}</span>}
          </>}
          <Button type="link" size="small" onClick={() => openReview(row)}>
            {review ? '修改结果' : '填写核对结果'}
          </Button>
        </Space>
      );
    },
  };

  const renderTable = (rows, emptyText, showReview = false) => (
    <Table
      size="small"
      rowKey="id"
      columns={showReview ? [...columns, reviewColumn] : columns}
      dataSource={rows}
      scroll={{ x: showReview ? 1415 : 1185 }}
      locale={{ emptyText }}
      pagination={{ pageSize: 10, hideOnSinglePage: true }}
      expandable={{
        rowExpandable: row => row.related.length > 0,
        expandedRowRender: row => (
          <Table
            size="small"
            rowKey="id"
            columns={identityColumns}
            dataSource={row.related}
            pagination={{ pageSize: 5, hideOnSinglePage: true }}
            title={() => '关联档案照片和身份资料'}
          />
        ),
      }}
    />
  );

  return (
    <>
    <Modal title="未来7天释放自检" visible onCancel={onClose} footer={null} width={1460}>
      {error && <Alert type="error" showIcon message="自检失败，请关闭窗口后重试。" />}
      {!error && !report && <Spin tip="正在检查档案" />}
      {report && (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Alert
            type={report.undated.length ? 'warning' : 'info'}
            showIcon
            message={`${report.start_date} 至 ${report.end_date} 预计刑满释放 ${report.rows.length} 人，${report.rows.filter(row => row.issues.length).length} 人有资料提醒`}
            description="同名和照片引用重复需要人工核对。点击照片可放大，展开有冲突的行可查看关联档案。"
          />
          <Tabs items={[
            {
              key: 'tomorrow',
              label: '未来7天名单',
              children: renderTable(report.rows, '未来7天暂无预计刑满释放人员', true),
            },
            {
              key: 'undated',
              label: `无法确定释放日期（${report.undated.length}）`,
              children: renderTable(report.undated, '没有刑期止日缺失或无法解析的在押档案'),
            },
          ]} />
        </Space>
      )}
    </Modal>
    <Modal
      title="填写人工核对结果"
      visible={Boolean(reviewing)}
      onCancel={() => setReviewing(null)}
      onOk={() => form.submit()}
      okText="保存"
      confirmLoading={saving}
      cancelButtonProps={{ disabled: saving }}
      closable={!saving}
      maskClosable={!saving}
      keyboard={!saving}
      forceRender
    >
      {reviewing && (
        <Space style={{ marginBottom: 16 }}>
          <Photo key={reviewing.photo_url} url={reviewing.photo_url} />
          <span>{reviewing.prisoner_name || '姓名缺失'} · {reviewing.prisoner_no || '编号缺失'}</span>
        </Space>
      )}
      <Form form={form} layout="vertical" onFinish={saveReview} disabled={saving}>
        <Form.Item name="decision" label="核对结论" rules={[{ required: true, message: '请选择核对结论' }]}>
          <Select
            placeholder="请选择"
            options={[
              { value: 'verified', label: '身份已核对' },
              { value: 'needs_review', label: '疑似重复或资料存疑，待复核' },
            ]}
          />
        </Form.Item>
        <Form.Item
          name="note"
          label="备注"
          dependencies={['decision']}
          rules={[({ getFieldValue }) => ({
            validator: (_, value) => getFieldValue('decision') !== 'needs_review' || value?.trim()
              ? Promise.resolve() : Promise.reject(new Error('请填写待复核原因')),
          })]}
        >
          <Input.TextArea rows={3} maxLength={500} showCount />
        </Form.Item>
      </Form>
      {saveError && <Alert type="error" showIcon message={saveError} />}
    </Modal>
    </>
  );
};

export default ReleaseCheck;
