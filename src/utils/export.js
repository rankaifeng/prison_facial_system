import { message } from 'antd';

const exportToCSV = (data, columns, filename) => {
  if (!data || data.length === 0) {
    message.warning('没有可导出的数据');
    return;
  }

  const headers = columns.map(col => col.title).join(',');
  const rows = data.map(row => {
    return columns.map(col => {
      let value = row[col.dataIndex];
      if (value === null || value === undefined) {
        value = '';
      }
      if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
        value = `"${value.replace(/"/g, '""')}"`;
      }
      return value;
    }).join(',');
  });

  const csvContent = '\uFEFF' + [headers, ...rows].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute('download', `${filename}_${new Date().toLocaleDateString('zh-CN').replace(/\//g, '-')}.csv`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  message.success('导出成功');
};

export default exportToCSV;