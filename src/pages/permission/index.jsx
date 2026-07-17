import React, { useState, useMemo } from 'react';
import { Button, message, Modal, Form, Input, Select, Popconfirm, Space } from 'antd';
import { PlusOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
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

  // 查看密码相关状态
  const [pwdModalVisible, setPwdModalVisible] = useState(false);
  const [pwdTargetId, setPwdTargetId] = useState(null);
  const [pwdTargetName, setPwdTargetName] = useState('');
  const [revealedPwd, setRevealedPwd] = useState('');
  const [pwdVerifying, setPwdVerifying] = useState(false);
  const [adminPwdForm] = Form.useForm();

  const { tableProps, form: searchForm, search, refresh } = useQueryTable({
    url: '/user_manage/account/account_list',
    rowKey: 'id',
  });

  const handleViewPassword = (record) => {
    setPwdTargetId(record.id);
    setPwdTargetName(record.username);
    setRevealedPwd('');
    adminPwdForm.resetFields();
    setPwdModalVisible(true);
  };

  const handleVerifyAdminPwd = async () => {
    try {
      const values = await adminPwdForm.validateFields();
      setPwdVerifying(true);
      const res = await http.post('/user_manage/account/get_password', {
        id: pwdTargetId,
        admin_password: values.admin_password,
      });
      if (res?.code === 1) {
        setRevealedPwd(res.data?.password || '');
      } else {
        message.error(res?.msg || '验证失败');
      }
    } catch (err) {
      if (err?.errorFields) return; // 表单验证失败
      message.error('请求失败');
    } finally {
      setPwdVerifying(false);
    }
  };

  const columns = [
    { title: '账号', dataIndex: 'username', key: 'username' },
    {
      title: '密码',
      key: 'password',
      width: 140,
      render: (_, record) => (
        <Space size={4}>
          <span style={{ color: '#bbb', letterSpacing: 2 }}>******</span>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewPassword(record)}
            style={{ padding: 0, fontSize: 12 }}
          >
            查看
          </Button>
        </Space>
      ),
    },
    { title: '所属监区', dataIndex: 'prison_name', key: 'prison_name' },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
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
      {/* 新增账号弹窗 */}
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
            <Input.Password placeholder={editingRecord ? '不修改请留空' : '请输入密码'} />
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

      {/* 查看密码弹窗 */}
      <Modal
        title={`查看密码 - ${pwdTargetName}`}
        open={pwdModalVisible}
        onCancel={() => { setPwdModalVisible(false); setRevealedPwd(''); adminPwdForm.resetFields(); }}
        footer={null}
        destroyOnClose
      >
        {!revealedPwd ? (
          <Form form={adminPwdForm} onFinish={handleVerifyAdminPwd} layout="vertical">
            <Form.Item
              name="admin_password"
              label="请输入管理员密码验证"
              rules={[{ required: true, message: '请输入管理员密码' }]}
            >
              <Input.Password placeholder="请输入当前管理员密码" />
            </Form.Item>
            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => { setPwdModalVisible(false); adminPwdForm.resetFields(); }}>取消</Button>
                <Button type="primary" htmlType="submit" loading={pwdVerifying}>验证</Button>
              </Space>
            </Form.Item>
          </Form>
        ) : (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ color: '#8c8c8c', marginBottom: 12, fontSize: 13 }}>账号密码</div>
            {revealedPwd ? (
              <div style={{
                fontSize: 20,
                fontWeight: 600,
                color: '#3b7dd8',
                background: '#f0f5fb',
                padding: '12px 24px',
                borderRadius: 8,
                letterSpacing: 1,
                fontFamily: 'monospace',
                display: 'inline-block',
              }}>
                {revealedPwd}
              </div>
            ) : (
              <div style={{ color: '#faad14', fontSize: 13 }}>
                该账号密码未存储，请通过重置密码功能设置新密码后即可查看
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AccountManagement;
