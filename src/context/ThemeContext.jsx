import React, { createContext, useContext, useState } from 'react';

export const ThemeContext = createContext({
  themeColor: '#3b7dd8',
  setThemeColor: () => {},
  layout: 'sider',
  setLayout: () => {},
});

export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider = ({ children }) => {
  const [themeColor, setThemeColor] = useState('#3b7dd8');
  const [layout, setLayout] = useState('sider');

  return (
    <ThemeContext.Provider value={{ themeColor, setThemeColor, layout, setLayout }}>
      {children}
    </ThemeContext.Provider>
  );
};
