import { Typography } from 'antd';
import jinghuiImg from '@/imgs/jinghui.png';

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
        gap: 10,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
        <img src={jinghuiImg} alt="警徽" style={{ width: 28, height: 28, borderRadius: '50%' }} />
      </div>
      {!collapsed && (
        <Text
          strong
          style={{
            color: '#fff',
            fontSize: 12,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          罪犯进出AB门人脸识别系统
        </Text>
      )}
    </div>
  );
};

export default Logo;
