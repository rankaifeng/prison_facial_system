import React, { useState, useMemo, useEffect } from 'react';
import { Button, message, Modal, Form, Input, Select } from 'antd';
import { LockOutlined, ExclamationCircleOutlined, PlusOutlined, EditOutlined } from '@ant-design/icons';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';
import http from '@/server/axios';
import cache from '@/utils/cache';

const { confirm } = Modal;

const AccountManagement = () => {
  const currentUser = cache.getVal("userName");
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
    { title: '账号', dataIndex: 'username', key: 'username', width: 150 },
    { title: '所属分监区', dataIndex: 'prison_name', key: 'prison_name', width: 120 },
    {
      title: '密码',
      dataIndex: 'password',
      key: 'password',
      width: 150,
      render: () => '********',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right',
      render: (_, record) => {
        const isAdmin = record.role === 'admin' || record.role_name === '管理员';
        const isSelf = record.name === currentUser;

        return (
          <>
            <Button
              type="link"
              icon={<EditOutlined />}
              disabled={isAdmin}
              onClick={() => handleEdit(record)}
            >
              编辑
            </Button>
          </>
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

  const handleEdit = (record) => {
    setEditingRecord(record);
    form.setFieldsValue({
      username: record.username,
      name: record.name,
      role: record.role,
      prison_id: record.prison_id,
    });
    setModalVisible(true);
  };

  const handleDelete = (record) => {
    confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除账号"${record.username}"吗？`,
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          await http.post('/prison_manage/account/account_delete', { id: record.id });
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

  const handleResetPassword = (record) => {
    confirm({
      title: '确认重置密码',
      icon: <ExclamationCircleOutlined />,
      content: `确定要重置 ${record.name} 的密码吗？重置后密码将恢复为默认密码：123456`,
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        setLoading(true);
        try {
          await http.post('/prison_manage/account/reset_password', { id: record.id });
          message.success('密码重置成功');
          refresh();
        } catch (error) {
          message.error('重置失败');
        } finally {
          setLoading(false);
        }
      },
    });
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