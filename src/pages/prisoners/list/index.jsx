import React, { useMemo } from 'react';
import { Button, message } from 'antd';
import { EyeOutlined, ExportOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';
import exportToCSV from '@/utils/export';

const PrisonerList = () => {
  const navigate = useNavigate();

  const { tableProps, loading, form, search } = useQueryTable({
    url: '/user_manage/archive/list',
    rowKey: 'bh',
  });

  const handleExport = () => {
    const data = tableProps.dataSource || [];
    if (data.length === 0) {
      message.warning('没有可导出的数据');
      return;
    }
    exportToCSV(data, columns.filter(col => col.key !== 'action'), '罪犯档案');
  };

  const columns = [
    { title: '罪犯编号', dataIndex: 'bh', key: 'bh', width: 120 },
    { title: '姓名', dataIndex: 'xm', key: 'xm', width: 100 },
    { title: '性别', dataIndex: 'xb', key: 'xb', width: 60 },
    { title: '年龄', dataIndex: 'age', key: 'age', width: 60 },
    { title: '民族', dataIndex: 'mz', key: 'mz', width: 80 },
    { title: '罪名', dataIndex: 'zm', key: 'zm', width: 120, ellipsis: true },
    { title: '原判刑期', dataIndex: 'ypxq', key: 'ypxq', width: 120, ellipsis: true },
    { title: '监区', dataIndex: 'db', key: 'db', width: 80 },
    { title: '监室号', dataIndex: 'jsh', key: 'jsh', width: 80 },
    { title: '入监日期', dataIndex: 'rjrq', key: 'rjrq', width: 120 },
    { title: '在押状态', dataIndex: 'zyxz', key: 'zyxz', width: 80 },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/prisoners/${record.bh}`)}
        >
          详情
        </Button>
      ),
    },
  ];

  const searchItems = useMemo(() => [
    {
      label: '罪犯编号',
      name: 'prisoner_no',
      type: 'input',
      props: { placeholder: '请输入罪犯编号' }
    },
    {
      label: '姓名',
      name: 'prisoner_name',
      type: 'input',
      props: { placeholder: '请输入姓名' }
    },
    {
      label: '监区',
      name: 'prison_area',
      type: 'input',
      props: { placeholder: '请输入监区' }
    },
    {
      label: '罪名',
      name: 'crime',
      type: 'input',
      props: { placeholder: '请输入罪名' }
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

export default PrisonerList;
