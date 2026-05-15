import {
  DashboardOutlined,
  TeamOutlined,
  FileTextOutlined,
  SafetyCertificateOutlined,
  AppstoreOutlined,
} from "@ant-design/icons";

export const allMenus = [
  {
    key: "/dashboard",
    icon: <DashboardOutlined />,
    label: "首页",
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
    key: "/permission",
    icon: <SafetyCertificateOutlined />,
    label: "账号管理",
  },
  {
    key: "/type-management",
    icon: <AppstoreOutlined />,
    label: "类型管理",
  },
];

export const getFirstMenuPath = () => {
  const firstMenu = allMenus[0];
  return firstMenu ? firstMenu.key : '/dashboard';
};
