import jinghuiImg from '@/imgs/jinghui.png';

const Logo = ({ collapsed }) => {
  return (
    <div
      style={{
        height: 64,
        display: 'flex',
        alignItems: 'center',
        justifyContent: collapsed ? 'center' : 'flex-start',
        padding: collapsed ? '0' : '0 12px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        gap: 8,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
        <img
          src={jinghuiImg}
          alt="警徽"
          style={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            boxShadow: '0 0 8px rgba(255,255,255,0.3)',
          }}
        />
      </div>
      {!collapsed && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <span
            style={{
              color: '#fff',
              fontSize: 14,
              fontWeight: 600,
              letterSpacing: 1,
              lineHeight: 1.4,
            }}
          >
            罪犯进出AB门
          </span>
          <span
            style={{
              color: 'rgba(255,255,255,0.75)',
              fontSize: 12,
              fontWeight: 400,
              letterSpacing: 2,
              lineHeight: 1.4,
            }}
          >
            人脸识别系统
          </span>
        </div>
      )}
    </div>
  );
};

export default Logo;
