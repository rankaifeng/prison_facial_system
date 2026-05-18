import React, { useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Button, message, Tag } from 'antd';
import { ExportOutlined, VideoCameraOutlined } from '@ant-design/icons';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';
import exportToCSV from '@/utils/export';

const Statistics = () => {
  const [searchParams] = useSearchParams();
  const prisonNameParam = searchParams.get('prisonName');

  const { tableProps, loading, form, search } = useQueryTable({
    url: '/user_manage/record/list',
    rowKey: 'id',
    defaultParams: prisonNameParam ? { prisonName: prisonNameParam } : {},
  });

  const handleExport = () => {
    const data = tableProps.dataSource || [];
    if (data.length === 0) {
      message.warning('没有可导出的数据');
      return;
    }
    exportToCSV(data, columns, '进出统计');
  };

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
      render: (val) => val ? (
        <img src="/imgs/face.png" alt="已确认" style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover' }} />
      ) : (
        <img src="/imgs/face.png" alt="未确认" style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover', opacity: 0.4 }} />
      ),
    },
    {
      title: '特警确认',
      dataIndex: 'swatConfirm',
      key: 'swatConfirm',
      width: 100,
      render: (val) => val ? (
        <img src="/imgs/face.png" alt="已确认" style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover' }} />
      ) : (
        <img src="/imgs/face.png" alt="未确认" style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover', opacity: 0.4 }} />
      ),
    },
    {
      title: '武警确认',
      dataIndex: 'armedPoliceConfirm',
      key: 'armedPoliceConfirm',
      width: 100,
      render: (val) => val ? (
        <img src="/imgs/face.png" alt="已确认" style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover' }} />
      ) : (
        <img src="/imgs/face.png" alt="未确认" style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover', opacity: 0.4 }} />
      ),
    },
    { title: '回监时间', dataIndex: 'returnTime', key: 'returnTime', width: 160 },
    {
      title: '监控录像',
      dataIndex: 'videoRecord',
      key: 'videoRecord',
      width: 120,
      render: (val) => val ? (
        <video
          src="https://www.w3schools.com/html/mov_bbb.mp4"
          controls
          style={{ width: 100, height: 50, objectFit: 'cover', borderRadius: 4 }}
        />
      ) : (
        <Tag color="default" icon={<VideoCameraOutlined />}>无录像</Tag>
      ),
    },
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

export default Statistics;
