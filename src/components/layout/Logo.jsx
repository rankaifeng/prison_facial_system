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
        gap: 10,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', flexShrink: 0, filter: 'drop-shadow(0 0 8px rgba(0, 240, 255, 0.5))' }}>
        <svg viewBox="0 0 32 32" width="24" height="24" fill="none">
          <path d="M16 2L4 8v8c0 7.7 5.1 14.9 12 16.8C22.9 30.9 28 23.7 28 16V8L16 2z" fill="rgba(0,240,255,0.15)" stroke="#00f0ff" strokeWidth="1.5"/>
          <path d="M16 6L7 10v6c0 5.8 3.8 11.2 9 12.6C21.2 27.2 25 21.8 25 16v-6L16 6z" fill="rgba(0,240,255,0.08)" stroke="rgba(0,240,255,0.4)" strokeWidth="1"/>
          <path d="M12 16l3 3 5-6" stroke="#00f0ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
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
