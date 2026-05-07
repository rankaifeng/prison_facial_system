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
        return <DatePicker style={{ width: 160 }} {...itemProps} />;
      case 'range':
        return <RangePicker style={{ width: 260 }} {...itemProps} />;
      case 'number':
        return <InputNumber style={{ width: 160 }} {...itemProps} />;
      case 'custom':
        return render ? render({ form }) : null;
      default:
        return <Input style={{ width: 160 }} allowClear {...itemProps} />;
    }
  };

  const handleFinish = (values) => {
    onSearch?.(values, form);
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
