import React from 'react';
import ReactDOM from 'react-dom/client';
import moment from 'moment';
import 'moment/locale/zh-cn';
import 'antd/dist/antd.less';
import App from './App';
import './styles/global.css';

// 过滤 antdv4 内部的警告（React 18.3+ / antd v5 兼容性问题）
const originalError = console.error;
console.error = (...args) => {
  const msg = args[0]?.toString?.() || '';
  if (msg.includes('defaultProps will be removed')) return;
  if (msg.includes('visible') && msg.includes('open')) return;
  if (msg.includes('useForm') && msg.includes('not connected')) return;
  if (msg.includes('Step is deprecated')) return;
  if (msg.includes('has been disposed')) return;
  originalError.apply(console, args);
};

const originalWarn = console.warn;
console.warn = (...args) => {
  const msg = args[0]?.toString?.() || '';
  if (msg.includes('defaultProps will be removed')) return;
  if (msg.includes('visible') && msg.includes('open')) return;
  if (msg.includes('useForm') && msg.includes('not connected')) return;
  if (msg.includes('Step is deprecated')) return;
  if (msg.includes('has been disposed')) return;
  originalWarn.apply(console, args);
};

// 设置 moment 全局中文
moment.locale('zh-cn');
moment.updateLocale('zh-cn', {
  months: '一月_二月_三月_四月_五月_六月_七月_八月_九月_十月_十一月_十二月'.split('_'),
  monthsShort: '1月_2月_3月_4月_5月_6月_7月_8月_9月_10月_11月_12月'.split('_'),
  weekdays: '星期日_星期一_星期二_星期三_星期四_星期五_星期六'.split('_'),
  weekdaysShort: '周日_周一_周二_周三_周四_周五_周六'.split('_'),
  weekdaysMin: '日_一_二_三_四_五_六'.split('_'),
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <App />
);
