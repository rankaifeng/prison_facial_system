import React, { useMemo } from 'react';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';

const ExitRecords = () => {
  const { tableProps, loading, form, search } = useQueryTable({
    url: '/prison_manage/exit_record/exit_record_list',
    rowKey: 'id',
  });

  const columns = [
    { title: '罪犯姓名', dataIndex: 'prisonerName', key: 'prisonerName', width: 100 },
    { title: '出监日期', dataIndex: 'exitDate', key: 'exitDate', width: 120 },
    { title: '出监原因', dataIndex: 'exitReason', key: 'exitReason', width: 120 },
    { title: '就医医院', dataIndex: 'hospital', key: 'hospital', width: 150 },
    {
      title: '民警确认',
      dataIndex: 'policeConfirm',
      key: 'policeConfirm',
      width: 100,
      render: (val) => val ? '✓' : '✗',
    },
    {
      title: '特警确认',
      dataIndex: 'swatConfirm',
      key: 'swatConfirm',
      width: 100,
      render: (val) => val ? '✓' : '✗',
    },
    {
      title: '武警确认',
      dataIndex: 'armedPoliceConfirm',
      key: 'armedPoliceConfirm',
      width: 100,
      render: (val) => val ? '✓' : '✗',
    },
    { title: '回监时间', dataIndex: 'returnTime', key: 'returnTime', width: 160 },
  ];

  const searchItems = useMemo(() => [
    {
      label: '罪犯姓名',
      name: 'prisonerName',
      type: 'input',
      props: { placeholder: '请输入罪犯姓名' }
    },
    {
      label: '出监原因',
      name: 'exitReason',
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
