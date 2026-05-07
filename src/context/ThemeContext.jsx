import React, { createContext, useContext, useState } from 'react';

export const ThemeContext = createContext({
  themeColor: '#1890ff',
  setThemeColor: () => {},
  layout: 'sider',
  setLayout: () => {},
});

export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider = ({ children }) => {
  const [themeColor, setThemeColor] = useState('#1890ff');
  const [layout, setLayout] = useState('sider');

  return (
    <ThemeContext.Provider value={{ themeColor, setThemeColor, layout, setLayout }}>
      {children}
    </ThemeContext.Provider>
  );
};
