import React, { useState, useMemo } from 'react';
import { Button, Modal, Form, Input, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';
import http from '@/server/axios';

const { confirm } = Modal;

const TypeManagement = () => {
  const [form] = Form.useForm();
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);

  const { tableProps, search, refresh } = useQueryTable({
    url: '/prison_manage/exit_type/exit_type_list',
    rowKey: 'id',
  });

  const columns = useMemo(() => [
    { title: '类型名称', dataIndex: 'type_name', key: 'type_name', width: 150 },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 160 },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <>
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
        </>
      ),
    },
  ], []);

  const searchItems = useMemo(() => [
    {
      label: '类型名称',
      name: 'type_name',
      type: 'input',
      props: { placeholder: '请输入类型名称' },
    },
  ], []);

  const handleAdd = () => {
    setEditingRecord(null);
    form.resetFields();
    form.setFieldsValue({ status: 'active', sort_order: 0 });
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    setEditingRecord(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleDelete = (record) => {
    confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除类型"${record.type_name}"吗？`,
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          await http.post('/prison_manage/exit_type/exit_type_delete', { id: record.id });
          message.success('删除成功');
          refresh();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const isEdit = !!editingRecord;
      const apiUrl = isEdit ? '/prison_manage/exit_type/exit_type_update' : '/prison_manage/exit_type/exit_type_add';
      const payload = isEdit ? { ...editingRecord, ...values } : values;
      await http.post(apiUrl, payload);
      message.success(isEdit ? '更新成功' : '新增成功');
      setModalVisible(false);
      refresh();
    } catch (error) {
      console.error('表单验证失败', error);
    }
  };

  return (
    <div>
      <SearchHeader
        form={form}
        items={searchItems}
        onSearch={search.submit}
        onReset={search.reset}
      />
      <TableLayout
        tableProps={tableProps}
        columns={columns}
        headerLayout={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新增类型
          </Button>
        }
      />
      <Modal
        title={editingRecord ? '编辑类型' : '新增类型'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        destroyOnClose
      >
        <Form form={form} layout="vertical" preserve={false}>
          <Form.Item
            name="type_name"
            label="类型名称"
            rules={[{ required: true, message: '请输入类型名称' }]}
          >
            <Input placeholder="请输入类型名称" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TypeManagement;