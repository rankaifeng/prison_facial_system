import React, { useMemo, useState, useEffect } from 'react';
import { Button, Image, message } from 'antd';
import { ExportOutlined } from '@ant-design/icons';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';
import exportToCSV from '@/utils/export';
import { recordExport } from '@/api/globApi';

const PRISON_AREAS = [
  { value: 1, label: '分监区一' },
  { value: 2, label: '分监区二' },
  { value: 3, label: '分监区三' },
  { value: 4, label: '分监区四' },
  { value: 5, label: '分监区五' },
  { value: 6, label: '分监区六' },
  { value: 7, label: '分监区七' },
];

const ReturnStatistics = () => {
  const [exitReasons, setExitReasons] = useState([]);
  const { tableProps, loading, form, search } = useQueryTable({
    url: '/user_manage/record/list',
    rowKey: 'id',
    defaultParams: { type: 'entry' },
  });
  const handleExport = async () => {
    const formValues = form.getFieldsValue();
    const params = {
      type: 'entry',
      ...formValues,
    };
    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === undefined || params[key] === '' || params[key] === null) {
        delete params[key];
      }
    });
    try {
      const res = await recordExport.get(params);
      exportToCSV(res, exportColumns, '回监统计');
    } catch (error) {
      message.error('导出失败');
    }
  };

  const exportColumns = [
    { title: '分监区', dataIndex: 'prison_area_name', key: 'prison_area_name' },
    { title: '罪犯姓名', dataIndex: 'prisoner_name', key: 'prisoner_name' },
    { title: '罪犯编号', dataIndex: 'prisoner_no', key: 'prisoner_no' },
    { title: '回监时间', dataIndex: 'entry_date', key: 'entry_date' },
    { title: '出监原因', dataIndex: 'exit_reason', key: 'exit_reason' },
    { title: '民警确认', dataIndex: 'police_face', key: 'police_face' },
  ];

  const columns = [
    { title: '分监区', dataIndex: 'prison_area_name', key: 'prison_area_name', width: 150 },
    { title: '罪犯姓名', dataIndex: 'prisoner_name', key: 'prisoner_name', width: 100 },
    { title: '罪犯编号', dataIndex: 'prisoner_no', key: 'prisoner_no', width: 120 },
    { title: '回监时间', dataIndex: 'entry_date', key: 'entry_date', width: 160 },
    {
      title: '民警确认',
      dataIndex: 'police_face',
      key: 'police_face',
      width: 100,
      render: (val) => {
        return <Image src={val} style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover' }} />
      }
    },
  ];

  const searchItems = useMemo(() => [
    {
      label: '分监区',
      name: 'prison_area',
      type: 'select',
      props: { placeholder: '请选择分监区', options: PRISON_AREAS }
    },
    {
      label: '罪犯姓名',
      name: 'prisoner_name',
      type: 'input',
      props: { placeholder: '请输入罪犯姓名' }
    },
    {
      label: '罪犯编号',
      name: 'prisoner_no',
      type: 'input',
      props: { placeholder: '请输入罪犯编号' }
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
        headerLayout={
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 10, gap: 12 }}>
            <Button type="primary" icon={<ExportOutlined />} onClick={handleExport}>
              导出
            </Button>
          </div>
        }
        tableProps={tableProps}
        loading={loading}
        columns={columns}
      />
    </div>
  );
};

export default ReturnStatistics;