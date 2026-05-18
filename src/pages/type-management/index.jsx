import React, { useMemo, useState } from 'react';
import { Button, Form, Input, Modal, Popconfirm, Space, message } from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  NodeIndexOutlined,
} from '@ant-design/icons';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';
import http from '@/server/axios';

const Account = [{ id: 1, name: '分监区一' },
{ id: 2, name: '分监区二' },
{ id: 3, name: '分监区三' },
{ id: 4, name: '分监区四' },
{ id: 5, name: '分监区五' },
{ id: 6, name: '分监区六' },
{ id: 7, name: '分监区七' }];


const TypeManagement = () => {
  const [modalForm] = Form.useForm();
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [parentRecord, setParentRecord] = useState(null);

  const { tableProps, loading, form: searchForm, search, refresh } = useQueryTable({
    url: '/prison_manage/exit_type/exit_type_list',
    rowKey: 'id',
    defaultPageSize: 10,
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
      message.success(res?.msg || (isEdit ? '更新成功' : '新增成功'));
      setModalVisible(false);
      refresh();
    } catch (error) {
      if (error?.errorFields) return;
      message.error(error?.response?.data?.msg || '保存失败');
    }
  };

  const columns = useMemo(() => [
    {
      title: '出监原因',
      dataIndex: 'type_name',
      key: 'type_name',
      render: (text, record) => (
        <Space>
          <span>{text}</span>
        </Space>
      ),
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      width: 300,
      render: (_, record) => (
        <>
          <Button
            type="link"
            size='small'
            icon={<NodeIndexOutlined />}
            onClick={() => handleAddChild(record)}
          >
            新增下级
          </Button>
          <Button
            size='small'
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            description={`确定要删除吗？`}
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
        </Form>
      </Modal>
    </div>
  );
};

export default TypeManagement;
