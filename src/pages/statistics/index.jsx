import React, { useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';

const Statistics = () => {
  const [searchParams] = useSearchParams();
  const prisonNameParam = searchParams.get('prisonName');

  const { tableProps, loading, form, search } = useQueryTable({
    url: '/prison_manage/exit_statistics/exit_statistics_list',
    rowKey: 'id',
    defaultParams: prisonNameParam ? { prisonName: prisonNameParam } : {},
  });

  const columns = [
    { title: '分监区', dataIndex: 'prisonName', key: 'prisonName', width: 150 },
    { title: '罪犯姓名', dataIndex: 'prisonerName', key: 'prisonerName', width: 100 },
    { title: '罪犯编号', dataIndex: 'prisonerNo', key: 'prisonerNo', width: 120 },
    { title: '出监时间', dataIndex: 'exitTime', key: 'exitTime', width: 160 },
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
    { title: '监控录像', dataIndex: 'videoRecord', key: 'videoRecord', ellipsis: true },
  ];

  const searchItems = useMemo(() => [
    {
      label: '分监区',
      name: 'prisonName',
      type: 'input',
      props: { placeholder: '请输入分监区名称' }
    },
    {
      label: '罪犯姓名',
      name: 'prisonerName',
      type: 'input',
      props: { placeholder: '请输入罪犯姓名' }
    },
    {
      label: '出监原因',
      name: 'exitReason',
      type: 'select',
      options: [
        { label: '刑期满释放', value: '刑期满释放' },
        { label: '减刑释放', value: '减刑释放' },
        { label: '假释', value: '假释' },
        { label: '保外就医', value: '保外就医' },
      ],
      props: { placeholder: '请选择出监原因' }
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
            <span style={{ fontSize: 16, fontWeight: 500 }}>
              {prisonNameParam ? `${prisonNameParam} - 进出统计` : '监狱进出统计'}
            </span>
          </div>
        }
        tableProps={tableProps}
        loading={loading}
        columns={columns}
      />
    </div>
  );
};

export default Statistics;
