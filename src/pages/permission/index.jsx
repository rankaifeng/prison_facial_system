import React, { useState, useMemo } from 'react';
import { Button, message, Modal } from 'antd';
import { LockOutlined, ExclamationCircleOutlined, PlusOutlined } from '@ant-design/icons';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';
import { account } from '@/api/globApi';
import cache from '@/utils/cache';

const { confirm } = Modal;

const Permission = () => {
  const currentUser = cache.getVal("userName");
  const [loading, setLoading] = useState(false);

  const { tableProps, form, search, refresh } = useQueryTable({
    url: '/prison_manage/account/account_list',
    rowKey: 'id',
  });

  const columns = [
    { title: '账号', dataIndex: 'username', key: 'username', width: 150 },
    { title: '姓名', dataIndex: 'name', key: 'name', width: 120 },
    { title: '角色', dataIndex: 'role', key: 'role', width: 100 },
    { title: '所属监狱', dataIndex: 'prison', key: 'prison', width: 120 },
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
      width: 120,
      fixed: 'right',
      render: (_, record) => {
        const isAdmin = record.role === '管理员';
        const isSelf = record.name === currentUser;

        return (
          <Button
            type="link"
            icon={<LockOutlined />}
            disabled={isAdmin || isSelf}
            onClick={() => handleResetPassword(record)}
          >
            重置密码
          </Button>
        );
      },
    },
  ];

  const searchItems = useMemo(() => [
    {
      label: '账号',
      name: 'username',
      type: 'input',
      props: { placeholder: '请输入账号' }
    },
    {
      label: '姓名',
      name: 'name',
      type: 'input',
      props: { placeholder: '请输入姓名' }
    },
    {
      label: '角色',
      name: 'role',
      type: 'select',
      options: [
        { label: '管理员', value: '管理员' },
        { label: '操作员', value: '操作员' },
        { label: '经理', value: '经理' },
      ],
      props: { placeholder: '请选择角色' }
    },
  ], []);

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
          await account.resetPwd({ id: record.id });
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
        form={form}
        items={searchItems}
        onSearch={search.submit}
        onReset={search.reset}
      />
      <TableLayout
        tableProps={tableProps}
        loading={loading}
        columns={columns}
      />
    </div>
  );
};

export default Permission;
