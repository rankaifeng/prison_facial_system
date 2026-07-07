import React, { useMemo, useState, useEffect } from 'react';
import { Button, Image, message, Tag, DatePicker } from 'antd';
import { ExportOutlined } from '@ant-design/icons';
import { useSearchParams } from 'react-router-dom';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import VideoPlayer from '@/components/video-player';
import useQueryTable from '@/hooks/useQueryTable';
import exportToExcel from '@/utils/export';
import { exitType, recordExport } from '@/api/globApi';

const { RangePicker } = DatePicker;

const PRISON_AREAS = [
  { value: 1, label: '一监区' },
  { value: 2, label: '二监区' },
  { value: 3, label: '三监区' },
  { value: 4, label: '四监区' },
  { value: 5, label: '五监区' },
  { value: 6, label: '六监区' },
  { value: 7, label: '七监区' },
];

const PRISON_AREA_MAP = {
  '一监区': 1,
  '二监区': 2,
  '三监区': 3,
  '四监区': 4,
  '五监区': 5,
  '六监区': 6,
  '七监区': 7,
};

const Statistics = () => {
  const [searchParams] = useSearchParams();
  const [exitReasons, setExitReasons] = useState([]);
  const [searchItems, setSearchItems] = useState([
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
    {
      label: '出监日期',
      name: 'date_range',
      type: 'dateRange',
      props: { placeholder: ['开始日期', '结束日期'] }
    },
  ])
  const { tableProps, loading, form, search } = useQueryTable({
    url: '/user_manage/record/list',
    rowKey: 'id',
    defaultParams: { type: 'exit' },
  });

  useEffect(() => {
    const prisonName = searchParams.get('prisonName');
    if (prisonName && PRISON_AREA_MAP[prisonName] && form) {
      const prisonAreaId = PRISON_AREA_MAP[prisonName];
      form.setFieldsValue({ prison_area: prisonAreaId });
      setTimeout(() => {
        search.submit({ prison_area: prisonAreaId });
      }, 0);
    }
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
    };
    // 处理日期范围（时间戳）
    if (formValues.date_range && formValues.date_range.length === 2) {
      params.start_timestamp = formValues.date_range[0].valueOf();
      params.end_timestamp = formValues.date_range[1].valueOf();
    }
    // 其他筛选条件
    if (formValues.prison_area) params.prison_area = formValues.prison_area;
    if (formValues.prisoner_name) params.prisoner_name = formValues.prisoner_name;
    if (formValues.prisoner_no) params.prisoner_no = formValues.prisoner_no;
    if (formValues.reason) params.reason = formValues.reason;
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
    { title: '监区', dataIndex: 'prison_area_name', key: 'prison_area_name' },
    { title: '罪犯姓名', dataIndex: 'prisoner_name', key: 'prisoner_name' },
    { title: '罪犯编号', dataIndex: 'prisoner_no', key: 'prisoner_no' },
    { title: '出监时间', dataIndex: 'exit_date', key: 'exit_date' },
    { title: '出监原因', dataIndex: 'reason', key: 'reason' },
    { title: '医院名称', dataIndex: 'hospital_name', key: 'hospital_name' },
    { title: '民警确认', dataIndex: 'police_face', key: 'police_face' },
    { title: '民警姓名', dataIndex: 'police_name', key: 'police_name' },
    { title: '特警确认', dataIndex: 'swat_face', key: 'swat_face' },
    { title: '特警姓名', dataIndex: 'swat_name', key: 'swat_name' },
    { title: '武警确认', dataIndex: 'armed_police_signature', key: 'armed_police_signature' },
    { title: '录像', dataIndex: 'video', key: 'video' },
  ];

  const columns = [
    { title: '监区', dataIndex: 'prison_area_name', key: 'prison_area_name', width: 150 },
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
    },{
      title: '民警姓名',
      dataIndex: 'police_name',
      key: 'police_name',
      width: 100,
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
      title: '特警姓名',
      dataIndex: 'swat_name',
      key: 'swat_name',
      width: 100,
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
      title: '武警照片',
      dataIndex: 'armed_police_face',
      key: 'armed_police_face',
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
      render: (_, record) => {
        return <VideoPlayer itemData={record} />
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
