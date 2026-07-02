import { SafetyOutlined } from '@ant-design/icons';
import { Typography } from 'antd';

const { Text } = Typography;

const Logo = ({ collapsed }) => {
  return (
    <div
      style={{
        height: 64,
        display: 'flex',
        alignItems: 'center',
        justifyContent: collapsed ? 'center' : 'flex-start',
        padding: collapsed ? '0' : '0 16px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
      }}
    >
      <SafetyOutlined style={{ fontSize: 24, color: '#1890ff' }} />
      {!collapsed && (
        <Text
          strong
          style={{
            color: '#fff',
            marginLeft: 8,
            fontSize: 16,
            whiteSpace: 'nowrap',
          }}
        >
          AB门人脸识别管理系统
        </Text>
      )}
    </div>
  );
};

export default Logo;
