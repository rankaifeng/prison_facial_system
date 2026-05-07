import { Breadcrumb } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import { HomeOutlined } from '@ant-design/icons';

const BreadcrumbMenu = () => {
  const location = useLocation();
  const pathSnippets = location.pathname.split('/').filter(i => i);

  const extraBreadcrumbItems = pathSnippets.map((snippet, index) => {
    const url = `/${pathSnippets.slice(0, index + 1).join('/')}`;
    const name = getNameFromPath(snippet);
    return {
      key: url,
      title: <Link to={url}>{name}</Link>,
    };
  });

  const breadcrumbItems = [
    {
      title: (
        <Link to="/">
          <HomeOutlined />
        </Link>
      ),
      key: 'home',
    },
    ...extraBreadcrumbItems,
  ];

  return <Breadcrumb items={breadcrumbItems} />;
};

const getNameFromPath = (path) => {
  const nameMap = {
    dashboard: '首页大屏',
    prisoners: '档案库',
    statistics: '进出统计',
    exitRecords: '出狱信息',
    permission: '权限管理',
    list: '列表',
    detail: '详情',
  };
  return nameMap[path] || path;
};

export default BreadcrumbMenu;
