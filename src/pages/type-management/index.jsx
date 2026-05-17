import React, { useMemo, useState } from 'react';
import { Button, Form, Input, InputNumber, Modal, Space, Tag, message } from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  NodeIndexOutlined,
} from '@ant-design/icons';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';
import http from '@/server/axios';

const { confirm } = Modal;

const TypeManagement = () => {
  const [modalForm] = Form.useForm();
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [parentRecord, setParentRecord] = useState(null);

  const { tableProps, loading, form: searchForm, search, refresh } = useQueryTable({
    url: '/prison_manage/exit_type/exit_type_list',
    rowKey: 'id',
    defaultPageSize: 100,
  });

  const handleAddRoot = () => {
    setEditingRecord(null);
    setParentRecord(null);
    modalForm.resetFields();
    modalForm.setFieldsValue({ sort_order: 0 });
    setModalVisible(true);
  };

  const handleAddChild = (record) => {
    setEditingRecord(null);
    setParentRecord(record);
    modalForm.resetFields();
    modalForm.setFieldsValue({ parent_id: record.id, sort_order: 0 });
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    setEditingRecord(record);
    setParentRecord(record.parent_id ? { id: record.parent_id, type_name: record.parent_name } : null);
    modalForm.resetFields();
    modalForm.setFieldsValue({
      type_name: record.type_name,
      sort_order: record.sort_order || 0,
      parent_id: record.parent_id,
    });
    setModalVisible(true);
  };

  const handleDelete = (record) => {
    confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除出监原因"${record.type_name}"吗？删除后它的下级原因也会一起删除。`,
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          const res = await http.post('/prison_manage/exit_type/exit_type_delete', { id: record.id });
          message.success(res?.message || '删除成功');
          refresh();
        } catch (error) {
          message.error(error?.response?.data?.message || '删除失败');
        }
      },
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await modalForm.validateFields();
      const isEdit = !!editingRecord;
      const apiUrl = isEdit ? '/prison_manage/exit_type/exit_type_update' : '/prison_manage/exit_type/exit_type_add';
      const payload = {
        ...(isEdit ? { id: editingRecord.id } : {}),
        type_name: values.type_name,
        parent_id: isEdit ? editingRecord.parent_id : parentRecord?.id,
        sort_order: values.sort_order || 0,
      };

      const res = await http.post(apiUrl, payload);
      message.success(res?.message || (isEdit ? '更新成功' : '新增成功'));
      setModalVisible(false);
      refresh();
    } catch (error) {
      if (error?.errorFields) return;
      message.error(error?.response?.data?.message || '保存失败');
    }
  };

  const columns = useMemo(() => [
    {
      title: '出监原因',
      dataIndex: 'type_name',
      key: 'type_name',
      width: 260,
      render: (text, record) => (
        <Space>
          <span>{text}</span>
          <Tag color={record.level === 1 ? 'blue' : record.level === 2 ? 'green' : 'default'}>
            {record.level}级
          </Tag>
        </Space>
      ),
    },
    { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 100 },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
    {
      title: '操作',
      key: 'action',
      width: 260,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<NodeIndexOutlined />}
            onClick={() => handleAddChild(record)}
          >
            新增下级
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ], []);

  const searchItems = useMemo(() => [
    {
      label: '出监原因',
      name: 'type_name',
      type: 'input',
      props: { placeholder: '请输入出监原因' },
    },
  ], []);

  return (
    <div>
      <SearchHeader
        form={searchForm}
        items={searchItems}
        onSearch={search.submit}
        onReset={search.reset}
      />
      <TableLayout
        tableProps={tableProps}
        loading={loading}
        columns={columns}
        headerLayout={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAddRoot}>
            新增一级原因
          </Button>
        }
      />
      <Modal
        title={editingRecord ? '编辑出监原因' : parentRecord ? `新增"${parentRecord.type_name}"的下级原因` : '新增一级出监原因'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        destroyOnClose
      >
        <Form form={modalForm} layout="vertical" preserve={false}>
          {parentRecord && (
            <Form.Item label="上级原因">
              <Input value={parentRecord.type_name} disabled />
            </Form.Item>
          )}
          <Form.Item
            name="type_name"
            label="出监原因"
            rules={[{ required: true, message: '请输入出监原因' }]}
          >
            <Input placeholder="请输入出监原因" />
          </Form.Item>
          <Form.Item name="sort_order" label="排序">
            <InputNumber style={{ width: '100%' }} min={0} precision={0} placeholder="数字越小越靠前" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TypeManagement;
