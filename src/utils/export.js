import { message } from 'antd';
import * as XLSX from 'xlsx';
import { Image } from 'antd';

const exportToExcel = (data, columns, filename) => {
  if (!data || data.length === 0) {
    message.warning('没有可导出的数据');
    return;
  }

  // 过滤掉 render 函数产生的额外字段，只保留 dataIndex 存在的列
  const exportColumns = columns.filter(col => col.dataIndex);

  // 构建表头
  const headers = exportColumns.map(col => col.title);

  // 构建数据行
  const rows = data.map(row => {
    return exportColumns.map(col => {
      let value = row[col.dataIndex];

      // 处理空值
      if (value === null || value === undefined) {
        value = '';
      }

      // 如果是图片URL，不转换，让Excel显示为链接
      return value;
    });
  });

  // 创建工作簿
  const wb = XLSX.utils.book_new();

  // 创建 worksheet 数据（包含表头）
  const wsData = [headers, ...rows];
  const ws = XLSX.utils.aoa_to_sheet(wsData);

  // 设置列宽
  ws['!cols'] = exportColumns.map((col, index) => {
    // 图片列更宽
    const isImage = col.dataIndex && (
      col.dataIndex.includes('face') ||
      col.dataIndex.includes('signature') ||
      col.dataIndex.includes('photo')
    );
    return { wch: isImage ? 25 : 15 };
  });

  XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');

  // 生成文件名
  const exportFilename = `${filename}_${new Date().toLocaleDateString('zh-CN').replace(/\//g, '-')}.xlsx`;

  // 触发下载
  XLSX.writeFile(wb, exportFilename);
  message.success('导出成功');
};

// 保留 CSV 导出以备后用
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

  const csvContent = '﻿' + [headers, ...rows].join('\n');
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

export { exportToExcel };
export default exportToCSV;