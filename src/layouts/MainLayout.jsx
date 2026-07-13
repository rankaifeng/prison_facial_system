import { useEffect, useState } from 'react';
import { Layout, Menu, Space, Modal } from 'antd';
import { SettingOutlined, LogoutOutlined, MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
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
  const [showMenus, setShowMenus] = useState([]);
  const navigate = useNavigate();
  const location = useLocation();
  const { layout } = useTheme();

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
            onClick={({ key }) => navigate(key)}
          >
            {showMenus.map(menu => (
              <Menu.Item key={menu.key} icon={menu.icon}>
                {menu.label}
              </Menu.Item>
            ))}
          </Menu>
        </Sider>
      )}
      <Layout
        style={{
          marginLeft: isDashboard ? 0 : (collapsed ? 80 : 220),
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
            <Space size={16}>
              <LogoutOutlined
                style={{ cursor: 'pointer', fontSize: 16, color: '#8c8c8c' }}
                onClick={handleLogout}
              />
            </Space>
          </Header>
        )}
        <Content
          style={{
            margin: 0,
            padding: 0,
            background: 'transparent',
            borderRadius: 0,
            overflow: 'hidden',
            height: isDashboard ? '100vh' : 'calc(100vh - 64px)',
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
