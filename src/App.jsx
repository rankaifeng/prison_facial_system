import React, { useState, createContext, useContext } from 'react';
import { BrowserRouter, useRoutes } from 'react-router-dom';
import routes from './router';
import AuthGuard from './router/AuthGuard';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/lib/locale/zh_CN';

export const ThemeContext = createContext({
  themeColor: '#1890ff',
  setThemeColor: () => {},
  layout: 'sider',
  setLayout: () => {},
});

export const useTheme = () => useContext(ThemeContext);

const AppContent = () => {
  const [themeColor, setThemeColor] = useState('#1890ff');
  const [layout, setLayout] = useState('sider');
  const element = useRoutes(routes);

  return (
    <ThemeContext.Provider value={{ themeColor, setThemeColor, layout, setLayout }}>
      <div style={{ '--ant-color-primary': themeColor }}>
        <ConfigProvider
          locale={zhCN}
          prefixCls="ant"
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
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
};

export default App;
