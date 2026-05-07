import { useState, useEffect } from 'react';
import { Layout, Menu, Avatar, Dropdown, Space, theme } from 'antd';
import { UserOutlined, SettingOutlined, LogoutOutlined } from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useTheme } from '@/context/ThemeContext';
import { allMenus } from '@/router/menus';
import cache from '@/utils/cache';
import Breadcrumb from '@/components/breadcrumb';
import Logo from '@/components/layout/Logo';

const { Header, Sider, Content } = Layout;

const MainLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { layout } = useTheme();
  const { token } = theme.useToken();

  const selectedKey = location.pathname;

  const userMenu = {
    items: [
      {
        key: 'changePwd',
        icon: <SettingOutlined />,
        label: '修改密码',
      },
      {
        type: 'divider',
      },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
      },
    ],
    onClick: ({ key }) => {
      if (key === 'logout') {
        cache.clearVal();
        navigate('/login');
      }
    },
  };

  return (
    <Layout style={{ height: '100vh', overflow: 'hidden' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={220}
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
          items={allMenus}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 220, transition: 'margin-left 0.2s', height: '100vh', overflow: 'hidden' }}>
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
              style={{ fontSize: 18, cursor: 'pointer' }}
            >
              {collapsed ? '☰' : '✕'}
            </span>
            <Breadcrumb />
          </Space>
          <Space size={16}>
            <Dropdown menu={userMenu}>
              <Space style={{ cursor: 'pointer' }}>
                <Avatar style={{ background: '#1890ff' }} icon={<UserOutlined />} />
                <span>{cache.getVal("userName") || '管理员'}</span>
              </Space>
            </Dropdown>
            <SettingOutlined
              style={{ cursor: 'pointer', fontSize: 16 }}
              onClick={() => setDrawerOpen(true)}
            />
          </Space>
        </Header>
        <Content
          style={{
            margin: 0,
            padding: 0,
            background: 'transparent',
            borderRadius: 0,
            overflow: 'hidden',
            height: 'calc(100vh - 64px)',
            flex: 1,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
