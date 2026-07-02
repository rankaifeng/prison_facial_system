import React, { useMemo, useState } from 'react';
import { Button, Form, Input, Modal, Popconfirm, message } from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';
import http from '@/server/axios';

const TypeManagement = () => {
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [form] = Form.useForm();

  const { tableProps, loading, form: searchForm, search, refresh } = useQueryTable({
    url: '/prison_manage/exit_type/exit_type_list',
    rowKey: 'id',
    defaultPageSize: 10,
  });

  const handleAdd = () => {
    setEditingRecord(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    setEditingRecord(record);
    form.setFieldsValue({ type_name: record.type_name });
    setModalVisible(true);
  };

  const handleDelete = async (record) => {
    try {
      const res = await http.post('/prison_manage/exit_type/exit_type_delete', { id: record.id });
      message.success(res?.msg || '删除成功');
      refresh();
    } catch (error) {
      message.error(error?.response?.data?.msg || '删除失败');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const isEdit = !!editingRecord;
      const apiUrl = isEdit ? '/prison_manage/exit_type/exit_type_update' : '/prison_manage/exit_type/exit_type_add';
      const payload = {
        ...(isEdit ? { id: editingRecord.id } : {}),
        type_name: values.type_name,
      };

      const res = await http.post(apiUrl, payload);
      message.success(res?.msg || (isEdit ? '更新成功' : '新增成功'));
      setModalVisible(false);
      refresh();
    } catch (error) {
      if (error?.errorFields) return;
      message.error(error?.response?.data?.msg || '保存失败');
    }
  };

  const columns = useMemo(() => [
    { title: '出监原因', dataIndex: 'type_name', key: 'type_name' },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <>
          <Button
            size='small'
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除吗？"
            onConfirm={() => handleDelete(record)}
            okText="确认"
            cancelText="取消"
          >
            <Button size='small' type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </>
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
        hideIndex
        headerLayout={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新增出监原因
          </Button>
        }
      />
      <Modal
        title={editingRecord ? '编辑出监原因' : '新增出监原因'}
        visible={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        destroyOnClose
      >
        <Form form={form} layout="vertical" preserve={false}>
          <Form.Item
            name="type_name"
            label="出监原因"
            rules={[{ required: true, message: '请输入出监原因' }]}
          >
            <Input placeholder="请输入出监原因" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TypeManagement;