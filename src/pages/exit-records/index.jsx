import React, { useMemo } from 'react';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import VideoPlayer from '@/components/video-player';
import useQueryTable from '@/hooks/useQueryTable';

const PRISON_AREAS = [
  { value: 1, label: '一监区' },
  { value: 2, label: '二监区' },
  { value: 3, label: '三监区' },
  { value: 4, label: '四监区' },
  { value: 5, label: '五监区' },
  { value: 6, label: '六监区' },
  { value: 7, label: '七监区' },
];

const ExitRecords = () => {
  const { tableProps, loading, form, search } = useQueryTable({
    url: '/user_manage/record/list',
    rowKey: 'id',
    defaultParams: { type: 'exit' },
  });

  const columns = [
    { title: '罪犯姓名', dataIndex: 'prisoner_name', key: 'prisoner_name', width: 100 },
    { title: '出监日期', dataIndex: 'exit_date', key: 'exit_date', width: 120 },
    { title: '出监原因', dataIndex: 'reason', key: 'reason', width: 120 },
    {
      title: '就医医院',
      dataIndex: 'hospital_name',
      key: 'hospital_name',
      width: 150,
      render: (val, record) => {
        if (record.reason === '外出就医' && val) {
          return val;
        }
        return '';
      }
    },
    {
      title: '民警确认',
      dataIndex: 'police_face',
      key: 'police_face',
      width: 100,
      render: (val) => val ? '✓' : '✗',
    },
    {
      title: '特警确认',
      dataIndex: 'swat_face',
      key: 'swat_face',
      width: 100,
      render: (val) => val ? '✓' : '✗',
    },
    {
      title: '武警确认',
      dataIndex: 'armed_police_signature',
      key: 'armed_police_signature',
      width: 100,
      render: (val) => val ? '✓' : '✗',
    },
    { title: '入监时间', dataIndex: 'entry_date', key: 'entry_date', width: 160 },
    {
      title: '录像',
      dataIndex: 'video',
      key: 'video',
      width: 100,
      render: (_, record) => {
        return <VideoPlayer
          startTime={record.start_time}
          endTime={record.end_time}
          cameraIndex={0}
        />
      }
    },
  ];

  const searchItems = useMemo(() => [
    {
      label: '监区',
      name: 'prison_area',
      type: 'select',
      props: { placeholder: '请选择监区', options: PRISON_AREAS }
    },
    {
      label: '罪犯姓名',
      name: 'prisoner_name',
      type: 'input',
      props: { placeholder: '请输入罪犯姓名' }
    },
    {
      label: '出监原因',
      name: 'reason',
      type: 'input',
      props: { placeholder: '请输入出监原因' }
    },
  ], []);

  return (
    <div>
      <SearchHeader
        form={form}
        items={searchItems}
        onSearch={search.submit}
        onReset={search.reset}
      />
      <TableLayout
        haderLayout={
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span style={{ fontSize: 16, fontWeight: 500 }}>罪犯出狱信息管理</span>
          </div>
        }
        tableProps={tableProps}
        loading={loading}
        columns={columns}
      />
    </div>
  );
};

export default ExitRecords;
