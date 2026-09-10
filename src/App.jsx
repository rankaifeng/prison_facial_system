import React, { useState, createContext, useContext } from 'react';
import { BrowserRouter, useRoutes } from 'react-router-dom';
import routes from './router';
import AuthGuard from './router/AuthGuard';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/lib/locale/zh_CN';

export const ThemeContext = createContext({
  themeColor: '#3b7dd8',
  setThemeColor: () => {},
  layout: 'sider',
  setLayout: () => {},
});

export const useTheme = () => useContext(ThemeContext);

const AppContent = () => {
  const [themeColor, setThemeColor] = useState('#3b7dd8');
  const [layout, setLayout] = useState('sider');
  const element = useRoutes(routes);

  return (
    <ThemeContext.Provider value={{ themeColor, setThemeColor, layout, setLayout }}>
      <div style={{ '--ant-color-primary': themeColor }}>
        <ConfigProvider
          locale={zhCN}
          prefixCls="ant"
          theme={{
            token: {
              colorPrimary: themeColor,
            },
            components: {
              Dropdown: {
                colorBgElevated: 'rgba(20, 25, 45, 0.98)',
                controlItemBgHover: 'rgba(255, 255, 255, 0.08)',
                controlItemBgActive: 'rgba(255, 255, 255, 0.06)',
                colorText: 'rgba(255, 255, 255, 0.85)',
                colorTextDescription: 'rgba(255, 255, 255, 0.55)',
              },
              Modal: {
                contentBg: 'rgba(14, 18, 35, 1)',
                headerBg: 'rgba(14, 18, 35, 1)',
                titleColor: 'rgba(255, 255, 255, 0.9)',
                colorText: 'rgba(255, 255, 255, 0.65)',
                colorIcon: 'rgba(255, 255, 255, 0.65)',
                colorIconHover: 'rgba(255, 255, 255, 0.9)',
                colorBgMask: 'rgba(0, 0, 0, 0.6)',
              },
            },
          }}
        >
          <AuthGuard>
            {element}
          </AuthGuard>
        </ConfigProvider>
      </div>
    </ThemeContext.Provider>
  );
};

const App = () => {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AppContent />
    </BrowserRouter>
  );
};

export default App;
