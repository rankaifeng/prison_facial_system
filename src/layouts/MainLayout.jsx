import { useEffect, useState } from 'react';
import { Layout, Menu, Space, Modal, Form, Input, Button, Tooltip, message } from 'antd';
import { LogoutOutlined, MenuFoldOutlined, MenuUnfoldOutlined, KeyOutlined } from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useTheme } from '@/context/ThemeContext';
import { allMenus } from '@/router/menus';
import cache from '@/utils/cache';
import Breadcrumb from '@/components/breadcrumb';
import Logo from '@/components/layout/Logo';
import { changePassword } from '@/api/globApi';

const { Header, Sider, Content } = Layout;

const MainLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [showMenus, setShowMenus] = useState([]);
  const [pwdModalOpen, setPwdModalOpen] = useState(false);
  const [pwdLoading, setPwdLoading] = useState(false);
  const [pwdForm] = Form.useForm();
  const navigate = useNavigate();
  const location = useLocation();
  const { layout } = useTheme();
  const userName = cache.getVal('roleName') || '用户';

  const selectedKey = location.pathname;
  const isDashboard = location.pathname === '/dashboard';

  const handleLogout = () => {
    Modal.confirm({
      title: '确认退出',
      content: '确定要退出登录吗？',
      okText: '确认',
      cancelText: '取消',
      onOk: () => {
        cache.clearVal();
        navigate('/login');
      },
    });
  };

  const handleChangePassword = async (values) => {
    if (values.new_password !== values.confirm_password) {
      message.error('两次输入的新密码不一致');
      return;
    }
    setPwdLoading(true);
    try {
      const res = await changePassword({
        old_password: values.old_password,
        new_password: values.new_password,
      });
      if (res?.code === 1) {
        message.success(res.msg);
        setPwdModalOpen(false);
        pwdForm.resetFields();
        setTimeout(() => {
          cache.clearVal();
          navigate('/login');
        }, 1000);
      } else {
        message.error(res?.msg || '修改失败');
      }
    } catch {
      message.error('请求失败');
    } finally {
      setPwdLoading(false);
    }
  };

  useEffect(() => {
    const mRole = cache.getVal('prisonName');
    if (mRole) {
      const filteredMenus = allMenus.filter(menu => menu.key !== '/permission' && menu.key !== '/type-management');
      setShowMenus(filteredMenus);
    } else {
      setShowMenus(allMenus);
    }
  }, [])

  return (
    <Layout style={{ height: '100vh', overflow: 'hidden' }}>
      {!isDashboard && (
        <Sider
          trigger={null}
          collapsible
          collapsed={collapsed}
          width={180}
          style={{
            overflow: 'auto',
            height: '100vh',
            position: 'fixed',
            left: 0,
            top: 0,
            bottom: 0,
            background: '#001529',
          }}
        >
          <Logo collapsed={collapsed} />
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[selectedKey]}
            onClick={({ key }) => navigate(key)}
            items={showMenus.map(menu => ({
              key: menu.key,
              icon: menu.icon,
              label: menu.label,
            }))}
          />
        </Sider>
      )}
      <Layout
        style={{
          marginLeft: isDashboard ? 0 : (collapsed ? 80 : 180),
          transition: 'margin-left 0.2s',
          height: '100vh',
          overflow: 'hidden',
        }}
      >
        {!isDashboard && (
          <Header
            style={{
              padding: '0 16px',
              background: '#fff',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
              position: 'sticky',
              top: 0,
              zIndex: 100,
              height: 64,
            }}
          >
            <Space>
              <span
                onClick={() => setCollapsed(!collapsed)}
                style={{ fontSize: 14, cursor: 'pointer', color: '#8c8c8c' }}
              >
                {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              </span>
              <Breadcrumb />
            </Space>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#f7f8fa', borderRadius: 20, padding: '4px 6px 4px 14px', border: '1px solid #e8e8e8' }}>
              <span style={{ fontSize: 13, color: '#595959', lineHeight: 1 }}>{userName}</span>
              <Tooltip title="修改密码">
                <span
                  style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28, borderRadius: '50%', cursor: 'pointer', transition: 'all 0.2s', color: '#8c8c8c' }}
                  onMouseEnter={e => { e.currentTarget.style.background = '#e6f0fb'; e.currentTarget.style.color = '#3b7dd8'; }}
                  onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#8c8c8c'; }}
                  onClick={() => setPwdModalOpen(true)}
                >
                  <KeyOutlined style={{ fontSize: 14 }} />
                </span>
              </Tooltip>
              <Tooltip title="退出登录">
                <span
                  style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28, borderRadius: '50%', cursor: 'pointer', transition: 'all 0.2s', color: '#8c8c8c' }}
                  onMouseEnter={e => { e.currentTarget.style.background = '#fff1f0'; e.currentTarget.style.color = '#ff4d4f'; }}
                  onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#8c8c8c'; }}
                  onClick={handleLogout}
                >
                  <LogoutOutlined style={{ fontSize: 14 }} />
                </span>
              </Tooltip>
            </div>
          </Header>
        )}
        <Content
          style={{
            margin: isDashboard ? 0 : 8,
            padding: 0,
            background: 'transparent',
            borderRadius: 0,
            overflow: 'hidden',
            height: isDashboard ? '100vh' : 'calc(100vh - 64px - 16px)',
            flex: 1,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
      <Modal
        title="修改密码"
        open={pwdModalOpen}
        onCancel={() => { setPwdModalOpen(false); pwdForm.resetFields(); }}
        footer={null}
        destroyOnClose
      >
        <Form form={pwdForm} onFinish={handleChangePassword} layout="vertical">
          <Form.Item name="old_password" label="旧密码" rules={[{ required: true, message: '请输入旧密码' }]}>
            <Input.Password placeholder="请输入旧密码" />
          </Form.Item>
          <Form.Item name="new_password" label="新密码" rules={[{ required: true, message: '请输入新密码' }, { min: 6, message: '密码至少6位' }]}>
            <Input.Password placeholder="请输入新密码" />
          </Form.Item>
          <Form.Item name="confirm_password" label="确认新密码" rules={[{ required: true, message: '请确认新密码' }]}>
            <Input.Password placeholder="请再次输入新密码" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => { setPwdModalOpen(false); pwdForm.resetFields(); }}>取消</Button>
              <Button type="primary" htmlType="submit" loading={pwdLoading}>确认修改</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  );
};

export default MainLayout;
