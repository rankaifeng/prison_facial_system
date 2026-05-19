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
    { title: '罪犯姓名', dataIndex: 'prisoner_name', key: 'prisoner_name', width: 100 },
    { title: '出监日期', dataIndex: 'exit_date', key: 'exit_date', width: 120 },
    { title: '出监原因', dataIndex: 'exit_reason', key: 'exit_reason', width: 120 },
    {
      title: '就医医院',
      dataIndex: 'hospital_name',
      key: 'hospital_name',
      width: 150,
      render: (val, record) => {
        if (record.exit_reason === '外出就医' && val) {
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
