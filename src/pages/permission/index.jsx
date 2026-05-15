import React, { useState, useMemo, useEffect } from 'react';
import { Button, message, Modal, Form, Input, Select, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';
import http from '@/server/axios';

const AccountManagement = () => {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [prisonAreas, setPrisonAreas] = useState([]);
  const [form] = Form.useForm();

  useEffect(() => {
    http.get('/prison_manage/prison_info/prison_info_list').then(res => {
      if (res?.data) {
        setPrisonAreas(res.data.map(p => ({ label: p.name, value: p.prison_id || p.id })));
      }
    });
  }, []);

  const { tableProps, form: searchForm, search, refresh } = useQueryTable({
    url: '/prison_manage/account/account_list',
    rowKey: 'id',
  });

  const columns = [
    { title: '账号', dataIndex: 'username', key: 'username'},
    { title: '所属分监区', dataIndex: 'prison_name', key: 'prison_name'},
    {
      title: '操作',
      fixed: 'right',
      width: 120,
      render: (_, record) => {
        const isAdmin = record.role === 'admin' || record.role_name === '管理员';
        return (
          <Popconfirm
            title="确认删除"
            description={`确定要删除账号"${record.username}"吗？`}
            onConfirm={async () => {
              try {
                await http.post('/prison_manage/account/account_delete', { id: record.id });
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
      const isEdit = !!editingRecord;
      const apiUrl = isEdit ? '/prison_manage/account/account_update' : '/prison_manage/account/account_add';
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
        open={modalVisible}
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
            label="所属分监区"
            rules={[{ required: true, message: '请选择分监区' }]}
          >
            <Select placeholder="请选择分监区" options={prisonAreas} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AccountManagement;