import React, { useMemo } from 'react';
import { Button, message } from 'antd';
import { EyeOutlined, PlusOutlined, ExportOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';
import exportToCSV from '@/utils/export';

const PrisonerList = () => {
  const navigate = useNavigate();

  const { tableProps, loading, form, search } = useQueryTable({
    url: '/prison_manage/prisoner_info/prisoner_info_list',
    rowKey: 'id',
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
    { title: '姓名', dataIndex: 'name', key: 'name', width: 100 },
    { title: '罪犯编号', dataIndex: 'prisonerNo', key: 'prisonerNo', width: 120 },
    { title: '年龄', dataIndex: 'age', key: 'age', width: 60 },
    { title: '性别', dataIndex: 'gender', key: 'gender', width: 60 },
    { title: '户籍地址', dataIndex: 'address', key: 'address', width: 200, ellipsis: true },
    { title: '身份证号', dataIndex: 'idCard', key: 'idCard', width: 180 },
    { title: '罪名', dataIndex: 'crime', key: 'crime', width: 120, ellipsis: true },
    { title: '刑期', dataIndex: 'sentence', key: 'sentence', width: 80 },
    {
      title: '刑期起止',
      key: 'sentencePeriod',
      width: 180,
      render: (_, record) => `${record.sentenceStart || ''} ~ ${record.sentenceEnd || ''}`,
    },
    { title: '入监日期', dataIndex: 'entryDate', key: 'entryDate', width: 120 },
    { title: '出监日期', dataIndex: 'releaseDate', key: 'releaseDate', width: 120 },
    { title: '刑满时间', dataIndex: 'releaseDate', key: 'releaseDate', width: 120 },
    { title: '刑期变动', dataIndex: 'releaseDate', key: 'releaseDate', width: 120 },
    { title: '亲属信息', dataIndex: 'releaseDate', key: 'releaseDate', width: 120 },
    {
      title: '操作',
      key: 'action',
      width: 80,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/prisoners/${record.id}`)}
        >
          详情
        </Button>
      ),
    },
  ];

  const searchItems = useMemo(() => [
    {
      label: '姓名',
      name: 'name',
      type: 'input',
      props: { placeholder: '请输入姓名' }
    },
    {
      label: '罪犯编号',
      name: 'prisonerNo',
      type: 'input',
      props: { placeholder: '请输入罪犯编号' }
    },
    {
      label: '性别',
      name: 'gender',
      type: 'select',
      options: [
        { label: '男', value: '男' },
        { label: '女', value: '女' },
      ],
      props: { placeholder: '请选择性别' }
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
