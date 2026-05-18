import React, { useMemo } from 'react';
import { Button, message, Tag } from 'antd';
import { ExportOutlined, VideoCameraOutlined } from '@ant-design/icons';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';
import exportToCSV from '@/utils/export';

const ReturnStatistics = () => {
  const { tableProps, loading, form, search } = useQueryTable({
    url: '/prison_manage/record/list',
    rowKey: 'id',
    defaultParams: { type: 'entry' },
  });

  const handleExport = () => {
    const data = tableProps.dataSource || [];
    if (data.length === 0) {
      message.warning('没有可导出的数据');
      return;
    }
    exportToCSV(data, columns, '回监统计');
  };

  const columns = [
    { title: '分监区', dataIndex: 'prison_area_name', key: 'prison_area_name', width: 150 },
    { title: '罪犯姓名', dataIndex: 'prisoner_name', key: 'prisoner_name', width: 100 },
    { title: '罪犯编号', dataIndex: 'prisoner_no', key: 'prisoner_no', width: 120 },
    { title: '回监时间', dataIndex: 'entry_date', key: 'entry_date', width: 160 },
    { title: '出监原因', dataIndex: 'exit_reason', key: 'exit_reason', width: 120 },
    {
      title: '民警确认',
      dataIndex: 'police_face',
      key: 'police_face',
      width: 100,
      render: (val) => val ? (
        <img src={val} alt="已确认" style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover' }} />
      ) : (
        <img src="/imgs/face.png" alt="未确认" style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover', opacity: 0.4 }} />
      ),
    },
  ];

  const searchItems = useMemo(() => [
    {
      label: '分监区',
      name: 'prison_area',
      type: 'input',
      props: { placeholder: '请输入分监区名称' }
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