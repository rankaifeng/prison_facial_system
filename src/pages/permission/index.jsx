import React, { useState, useMemo, useEffect } from 'react';
import { Button, message, Modal, Form, Input, Select, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';
import http from '@/server/axios';

const prisonAreas = [{ id: 1, name: '一监区' },
{ id: 2, name: '二监区' },
{ id: 3, name: '三监区' },
{ id: 4, name: '四监区' },
{ id: 5, name: '五监区' },
{ id: 6, name: '六监区' },
{ id: 7, name: '七监区' }];

const AccountManagement = () => {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [form] = Form.useForm();


  const { tableProps, form: searchForm, search, refresh } = useQueryTable({
    url: '/user_manage/account/account_list',
    rowKey: 'id',
  });

  const columns = [
    { title: '账号', dataIndex: 'username', key: 'username' },
    { title: '所属监区', dataIndex: 'prison_name', key: 'prison_name' },
    {
      title: '操作',
      width: 120,
      render: (_, record) => {
        const isAdmin = record.role === 'admin' || record.role_name === '管理员';
        return (
          <Popconfirm
            title={`确定要删除账号"${record.username}"吗？`}
            onConfirm={async () => {
              try {
                await http.post('/user_manage/account/account_delete', { id: record.id });
                message.success('删除成功');
                refresh();
              } catch (error) {
                message.error('删除失败');
              }
            }}
            okText="确认"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              disabled={isAdmin}
            >
              删除
            </Button>
          </Popconfirm>
        );
      },
    },
  ];

  const searchItems = useMemo(() => [
    {
      label: '账号',
      name: 'username',
      type: 'input',
      props: { placeholder: '请输入账号' },
    },
  ], []);

  const handleAdd = () => {
    setEditingRecord(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      await http.post('/user_manage/account/account_add', values);
      message.success('新增成功');
      setModalVisible(false);
      refresh();
    } catch (error) {
      console.error('表单验证失败', error);
    }
  };


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
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新增账号
          </Button>
        }
      />
      <Modal
        title={editingRecord ? '编辑账号' : '新增账号'}
        visible={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        destroyOnClose
      >
        <Form form={form} layout="vertical" preserve={false}>
          <Form.Item
            name="username"
            label="账号"
            rules={[{ required: true, message: '请输入账号' }]}
          >
            <Input placeholder="请输入账号" disabled={!!editingRecord} />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: !editingRecord, message: '请输入密码' }]}
          >
            <Input type="password" placeholder={editingRecord ? '不修改请留空' : '请输入密码'} />
          </Form.Item>

          <Form.Item
            name="prison_id"
            label="所属监区"
            rules={[{ required: true, message: '请选择监区' }]}
          >
            <Select placeholder="请选择监区" options={prisonAreas} fieldNames={{ label: 'name', value: 'id' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AccountManagement;