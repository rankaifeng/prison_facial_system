import React, { useMemo } from 'react';
import { Form, Input, Button, Select, DatePicker, InputNumber, Space, TreeSelect } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';

const { RangePicker } = DatePicker;

const SearchHeader = (props) => {
  const {
    form: externalForm,
    items = [],
    onSearch,
    onReset,
    submitText = '查询',
    resetText = '重置',
    layout = 'inline',
    gutter = [12, 12],
    style,
  } = props || {};

  const form = externalForm ? externalForm : Form.useForm()[0];

  const renderItem = (item) => {
    const { type = 'input', fieldNames, name, label, props: itemProps = {}, options = [], render, treeData = [] } = item;
    switch (type) {
      case 'input':
        return <Input style={{ width: 160 }} allowClear {...itemProps} />;
      case 'select':
        return <Select fieldNames={fieldNames} style={{ width: 160 }} allowClear options={options} {...itemProps} />;
      case 'treeSelect':
        return <TreeSelect style={{ width: 200 }} allowClear fieldNames={fieldNames} treeData={treeData} {...itemProps} />;
      case 'date':
        return <DatePicker style={{ width: 3300 }} {...itemProps} />;
      case 'dateRange':
        return <RangePicker style={{ width: 320 }} {...itemProps} showTime format="YYYY-MM-DD HH:mm" />;
      case 'range':
        return <RangePicker style={{ width: 320 }} {...itemProps} />;
      case 'number':
        return <InputNumber style={{ width: 160 }} {...itemProps} />;
      case 'custom':
        return render ? render({ form }) : null;
      default:
        return <Input style={{ width: 160 }} allowClear {...itemProps} />;
    }
  };

  const handleFinish = (values) => {
    // 处理 dateRange 类型字段，拆分为 start_timestamp 和 end_timestamp（时间戳）
    const processedValues = { ...values };
    Object.keys(processedValues).forEach(key => {
      const item = items.find(i => i.name === key);
      if (item?.type === 'dateRange') {
        const val = processedValues[key];
        // 支持数组格式 [start, end]
        if (Array.isArray(val) && val.length === 2) {
          const [start, end] = val;
          // dayjs 或 moment 对象，使用 valueOf() 获取时间戳
          const startTs = start?.valueOf ? start.valueOf() : new Date(start).getTime();
          const endTs = end?.valueOf ? end.valueOf() : new Date(end).getTime();
          processedValues.start_timestamp = String(startTs);
          processedValues.end_timestamp = String(endTs);
        } else if (typeof val === 'string') {
          // 字符串格式：start,end
          const parts = val.split(',');
          if (parts.length === 2) {
            processedValues.start_timestamp = parts[0].trim();
            processedValues.end_timestamp = parts[1].trim();
          }
        }
        // 完全删除 date_range 相关的键，避免残留
        delete processedValues[key];
      }
    });
    // 移除空值
    Object.keys(processedValues).forEach(key => {
      if (processedValues[key] === undefined || processedValues[key] === '' || processedValues[key] === null) {
        delete processedValues[key];
      }
    });
    // 直接调用搜索，不通过 Form 的 onFinish（避免表单值被重新使用）
    onSearch?.(processedValues, form);
  };

  const handleReset = () => {
    form.resetFields();
    onReset?.(form);
  };

  const nodes = useMemo(() => {
    return items.map((item) => {
      const { name, label } = item;
      return (
        <div style={{ margin: '5px' }} key={item?.name}>
          <Form.Item label={label} name={name}>
            {renderItem(item)}
          </Form.Item>
        </div>
      );
    });
  }, [items]);

  return (
    <div className='search-header' style={{ background: '#fff', padding: 12, borderRadius: 8, width: '100%', margin: '0 0 12px 0', boxShadow: '0 1px 3px rgba(0, 0, 0, 0.06)', ...style }}>
      <Form
        form={form}
        layout={layout}
        onFinish={handleFinish}
      >
        {nodes}
        <Space wrap style={{ marginLeft: 8 }}>
          <Button icon={<SearchOutlined />} type="primary" htmlType="submit">{submitText}</Button>
          <Button icon={<ReloadOutlined />} onClick={handleReset}>{resetText}</Button>
        </Space>
      </Form>
    </div>
  );
};

export default SearchHeader;
