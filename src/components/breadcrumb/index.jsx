import { Breadcrumb } from 'antd';
import { useLocation, Link } from 'react-router-dom';
import { HomeOutlined } from '@ant-design/icons';

const BreadcrumbMenu = () => {
  const location = useLocation();
  const pathSnippets = location.pathname.split('/').filter(i => i);

  return (
    <Breadcrumb>
      <Breadcrumb.Item>
        <Link to="/dashboard"><HomeOutlined /></Link>
      </Breadcrumb.Item>
      {pathSnippets.map((snippet, index) => {
        const url = `/${pathSnippets.slice(0, index + 1).join('/')}`;
        const name = getNameFromPath(snippet);
        return (
          <Breadcrumb.Item key={url}>
            <Link to={url}>{name}</Link>
          </Breadcrumb.Item>
        );
      })}
    </Breadcrumb>
  );
};

const getNameFromPath = (path) => {
  const nameMap = {
    dashboard: '首页大屏',
    prisoners: '档案库',
    statistics: '出监统计',
    'return-records': '回监统计',
    permission: '账号管理',
    'type-management': '出监原因管理',
    list: '列表',
    detail: '详情',
  };
  return nameMap[path] || path;
};

export default BreadcrumbMenu;
