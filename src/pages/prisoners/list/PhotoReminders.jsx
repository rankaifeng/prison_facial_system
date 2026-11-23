import React, { useState } from 'react';
import { Alert, Button, Modal, Select, Space, Table, Tag } from 'antd';
import { useRequest } from 'ahooks';
import http from '@/server/axios';

export const photoStatuses = {
  missing: { label: '缺少正面照', color: 'error' },
  invalid: { label: '照片地址异常', color: 'error' },
  expired: { label: '入监满五年，待更新', color: 'warning' },
  date_unknown: { label: '入监日期待核实', color: 'warning' },
  current: { label: '有照片，入监未满五年', color: 'success' },
};

const loadReminders = async () => {
  const result = await http.get('/user_manage/archive/photo-reminders');
  if (result.code !== 1 || !Array.isArray(result.data)) throw new Error('照片提醒查询失败');
  return { rows: result.data, areas: result.areas || [] };
};

const PhotoReminders = ({ onViewArchive }) => {
  const [open, setOpen] = useState(false);
  const [area, setArea] = useState();
  const { data, loading, error, refresh } = useRequest(loadReminders);
  const reminders = data?.rows || [];
  const areas = data?.areas || [];
  const rows = area ? reminders.filter(row => row.prison_area === area) : reminders;
  const columns = [
    { title: '监区', dataIndex: 'prison_area', width: 100 },
    { title: '姓名', dataIndex: 'prisoner_name', width: 90 },
    { title: '罪犯编号', dataIndex: 'prisoner_no', width: 125 },
    {
      title: '照片状态', dataIndex: 'status', width: 170,
      render: status => <Tag color={photoStatuses[status].color}>{photoStatuses[status].label}</Tag>,
    },
    { title: '入监日期', dataIndex: 'entry_date', width: 115, render: value => value || '—' },
    { title: '处理事项', dataIndex: 'action' },
    {
      title: '档案', key: 'archive', width: 75,
      render: (_, row) => <Button type="link" onClick={() => onViewArchive(row.prisoner_no)}>查看</Button>,
    },
  ];

  return (
    <>
      <Alert
        style={{ marginBottom: 12 }}
        type={error || reminders.length ? 'warning' : 'info'}
        showIcon
        message={error ? '照片维护提醒加载失败' : loading ? '正在查询照片维护提醒' : `照片维护待处理 ${reminders.length} 人`}
        action={<Button size="small" onClick={() => { setArea(undefined); setOpen(true); refresh(); }}>查看照片维护提醒</Button>}
      />
      <Modal title="监区照片维护提醒" visible={open} onCancel={() => setOpen(false)} footer={null} width={1060}>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Alert
            type="info"
            showIcon
            message="所属监区负责补采或更新照片。五年从入监日期起算，日期不明确时请核实档案。"
          />
          <Space>
            <Select
              aria-label="筛选监区"
              placeholder="全部可见监区"
              style={{ width: 175 }}
              allowClear
              value={area}
              onChange={setArea}
              loading={loading}
              notFoundContent={loading ? '正在加载监区' : '此账号暂无可查看的监区'}
              options={areas.map(name => ({ value: name, label: name }))}
            />
            <Button onClick={refresh} loading={loading}>刷新名单</Button>
          </Space>
          {error ? <Alert type="error" message="照片维护提醒加载失败，请刷新重试。" /> : (
            <Table
              rowKey="prisoner_no"
              size="small"
              columns={columns}
              dataSource={rows}
              loading={loading}
              pagination={{ pageSize: 10, hideOnSinglePage: true }}
              scroll={{ x: 940 }}
              locale={{ emptyText: area ? `${area}没有需要处理的照片记录` : '当前没有需要处理的照片记录' }}
            />
          )}
        </Space>
      </Modal>
    </>
  );
};

export default PhotoReminders;
