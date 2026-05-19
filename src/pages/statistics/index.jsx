import React, { useMemo, useState, useEffect } from 'react';
import { Button, Image, message, Tag } from 'antd';
import { ExportOutlined } from '@ant-design/icons';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import VideoPlayer from '@/components/video-player';
import useQueryTable from '@/hooks/useQueryTable';
import exportToExcel from '@/utils/export';
import { exitType, recordExport } from '@/api/globApi';

const PRISON_AREAS = [
  { value: 1, label: '分监区一' },
  { value: 2, label: '分监区二' },
  { value: 3, label: '分监区三' },
  { value: 4, label: '分监区四' },
  { value: 5, label: '分监区五' },
  { value: 6, label: '分监区六' },
  { value: 7, label: '分监区七' },
];

const Statistics = () => {
  const [exitReasons, setExitReasons] = useState([]);
  const [searchItems, setSearchItems] = useState([
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
    {
      label: '出监原因',
      name: 'reason',
      type: 'select',
      props: { placeholder: '请选择出监原因', options: [] }
    },
  ])
  const { tableProps, loading, form, search } = useQueryTable({
    url: '/user_manage/record/list',
    rowKey: 'id',
    defaultParams: { type: 'exit' },
  });

  useEffect(() => {
    const fetchExitTypes = async () => {
      try {
        const res = await exitType.list();
        console.log('exitType.list res:', res);
        console.log('Array.isArray(res):', Array.isArray(res));
        if (res && Array.isArray(res)) {
          console.log('Setting exitReasons');
          const options = res.map(item => ({
            value: item.type_name,
            label: item.type_name,
          }));
          setSearchItems(prevItems => prevItems.map(item => {
            if (item.name === 'reason') {
              return { ...item, props: { ...item.props, options } };
            }
            return item;
          }));
        } else {
          console.log('res is not array or is empty:', res);
        }
      } catch (error) {
        console.error('获取出监原因列表失败', error);
      }
    };
    fetchExitTypes();
  }, []);

  console.log('exitReasons state:', exitReasons);

  const handleExport = async () => {
    const formValues = form.getFieldsValue();
    const params = {
      type: 'exit',
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
      if (res && res.length > 0) {
        exportToExcel(res, exportColumns, '出监统计');
      } else {
        message.warning('没有可导出的数据');
      }
    } catch (error) {
      message.error('导出失败');
    }
  };

  const exportColumns = [
    { title: '分监区', dataIndex: 'prison_area_name', key: 'prison_area_name' },
    { title: '罪犯姓名', dataIndex: 'prisoner_name', key: 'prisoner_name' },
    { title: '罪犯编号', dataIndex: 'prisoner_no', key: 'prisoner_no' },
    { title: '出监时间', dataIndex: 'exit_date', key: 'exit_date' },
    { title: '出监原因', dataIndex: 'reason', key: 'reason' },
    { title: '医院名称', dataIndex: 'hospital_name', key: 'hospital_name' },
    { title: '民警确认', dataIndex: 'police_face', key: 'police_face' },
    { title: '特警确认', dataIndex: 'swat_face', key: 'swat_face' },
    { title: '武警确认', dataIndex: 'armed_police_signature', key: 'armed_police_signature' },
    { title: '录像', dataIndex: 'video', key: 'video' },
  ];

  const columns = [
    { title: '分监区', dataIndex: 'prison_area_name', key: 'prison_area_name', width: 150 },
    { title: '罪犯姓名', dataIndex: 'prisoner_name', key: 'prisoner_name', width: 100 },
    { title: '罪犯编号', dataIndex: 'prisoner_no', key: 'prisoner_no', width: 120 },
    { title: '出监时间', dataIndex: 'exit_date', key: 'exit_date', width: 160 },
    {
      title: '出监原因',
      width: 120,
      render: (v) => {
        return (
          <Tag color='blue'>
            {v?.reason} {v?.hospital_name && '-' + v?.hospital_name}
          </Tag>
        )
      }
    },
    {
      title: '民警确认',
      dataIndex: 'police_face',
      key: 'police_face',
      width: 100,
      render: (val) => {
        return <Image src={val} style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover' }} />
      }
    },
    {
      title: '特警确认',
      dataIndex: 'swat_face',
      key: 'swat_face',
      width: 100,
      render: (val) => {
        return <Image src={val} style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover' }} />
      }
    },
    {
      title: '武警确认',
      dataIndex: 'armed_police_signature',
      key: 'armed_police_signature',
      width: 100,
      render: (val) => {
        return <Image src={val} style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover' }} />
      }
    },
    {
      title: '录像',
      dataIndex: 'video',
      key: 'video',
      width: 100,
      render: (val) => {
        return <VideoPlayer src={val} />
      }
    },
  ];



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
