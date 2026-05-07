import {
  DashboardOutlined,
  TeamOutlined,
  FileTextOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";

export const allMenus = [
  {
    key: "/dashboard",
    icon: <DashboardOutlined />,
    label: "首页大屏",
  },
  {
    key: "/prisoners",
    icon: <TeamOutlined />,
    label: "档案库",
  },
  {
    key: "/statistics",
    icon: <FileTextOutlined />,
    label: "进出统计",
  },
  {
    key: "/exit-records",
    icon: <FileTextOutlined />,
    label: "出狱信息",
  },
  {
    key: "/permission",
    icon: <SafetyCertificateOutlined />,
    label: "权限管理",
  },
];

export const getFirstMenuPath = () => {
  const firstMenu = allMenus[0];
  return firstMenu ? firstMenu.key : '/dashboard';
};
