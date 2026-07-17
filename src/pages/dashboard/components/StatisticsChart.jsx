import React, { useState, useEffect, useRef } from 'react';
import {
  EnvironmentOutlined,
  BankOutlined,
  ShopOutlined,
  HomeOutlined,
  MedicineBoxOutlined,
  ReadOutlined,
  ToolOutlined,
  SafetyOutlined,
  BuildOutlined,
} from '@ant-design/icons';

// 所有监区列表
const ALL_PRISON_AREAS = [
  '一监区', '二监区', '三监区', '四监区',
  '五监区', '六监区', '七监区', '八监区'
];

// 监区图标和颜色配置
const AREA_CONFIG = {
  '一监区': { icon: <BuildOutlined />, color: '#00f0ff', bgColor: 'rgba(0, 240, 255, 0.15)' },
  '二监区': { icon: <BankOutlined />, color: '#3b7dd8', bgColor: 'rgba(59, 125, 216, 0.15)' },
  '三监区': { icon: <HomeOutlined />, color: '#52c41a', bgColor: 'rgba(82, 196, 26, 0.15)' },
  '四监区': { icon: <MedicineBoxOutlined />, color: '#faad14', bgColor: 'rgba(250, 173, 20, 0.15)' },
  '五监区': { icon: <ReadOutlined />, color: '#722ed1', bgColor: 'rgba(114, 46, 209, 0.15)' },
  '六监区': { icon: <ShopOutlined />, color: '#eb2f96', bgColor: 'rgba(235, 47, 150, 0.15)' },
  '七监区': { icon: <ToolOutlined />, color: '#fa8c16', bgColor: 'rgba(250, 140, 22, 0.15)' },
  '八监区': { icon: <SafetyOutlined />, color: '#13c2c2', bgColor: 'rgba(19, 194, 194, 0.15)' },
};

// 计数动画 Hook
const useCountUp = (target, duration = 1000, delay = 0) => {
  const [count, setCount] = useState(0);
  const startTimeRef = useRef(null);
  const frameRef = useRef(null);

  useEffect(() => {
    if (target === 0) {
      setCount(0);
      return;
    }

    const timeout = setTimeout(() => {
      const animate = (timestamp) => {
        if (!startTimeRef.current) startTimeRef.current = timestamp;
        const progress = Math.min((timestamp - startTimeRef.current) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        setCount(Math.floor(eased * target));

        if (progress < 1) {
          frameRef.current = requestAnimationFrame(animate);
        }
      };

      frameRef.current = requestAnimationFrame(animate);
    }, delay);

    return () => {
      clearTimeout(timeout);
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, [target, duration, delay]);

  return count;
};

// 带计数动画的数字组件
const AnimatedNumber = ({ value, color, delay }) => {
  const animatedValue = useCountUp(value, 800, delay);

  return (
    <span style={{
      color: color,
      fontWeight: 700,
      fontSize: '16px',
      textShadow: value > 0 ? `0 0 10px ${color}66` : 'none',
      fontVariantNumeric: 'tabular-nums',
    }}>
      {animatedValue}
    </span>
  );
};

const StatisticsChart = ({ data }) => {
  const exitCount = data?.total?.exit_count || 0;
  const byArea = data?.by_area || [];
  const [animated, setAnimated] = useState(false);

  // 构建监区数据映射
  const areaMap = {};
  byArea.forEach(area => {
    areaMap[area.prison_area_name] = area.exit_count || 0;
  });

  // 确保所有监区都显示，没有数据的显示 0
  const allAreas = ALL_PRISON_AREAS.map(name => ({
    prison_area_name: name,
    exit_count: areaMap[name] || 0
  })).sort((a, b) => b.exit_count - a.exit_count);

  // 入场动画
  useEffect(() => {
    const timer = setTimeout(() => setAnimated(true), 100);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="statistics-chart">
      <div className="chart-header">
        <div className="header-content">
          <EnvironmentOutlined />
          <span>当日各监区出监统计</span>
        </div>
        <div className="header-line"></div>
        <div className="header-decor">
          <span className="decor-dot"></span>
          <span className="decor-dot"></span>
          <span className="decor-dot"></span>
        </div>
      </div>
      <div className="chart-content">
        <div className="exit-reason-list">
          {allAreas.map((area, i) => {
            const config = AREA_CONFIG[area.prison_area_name] || { icon: <BuildOutlined />, color: '#00f0ff', bgColor: 'rgba(0, 240, 255, 0.15)' };
            const percentage = exitCount > 0 ? (area.exit_count / exitCount) * 100 : 0;

            return (
              <div
                key={i}
                className="exit-reason-row"
                style={{
                  opacity: animated ? 1 : 0,
                  transform: animated ? 'translateX(0)' : 'translateX(-20px)',
                  transition: `all 0.5s ease ${i * 0.1}s`,
                  padding: '2px 0',
                }}
              >
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  minWidth: '100px',
                }}>
                  <span className="area-icon" style={{
                    fontSize: '16px',
                    color: config.color,
                    display: 'flex',
                    alignItems: 'center',
                    animation: `iconBreathe 3s ease-in-out ${i * 0.2}s infinite`,
                  }}>
                    {config.icon}
                  </span>
                  <span style={{
                    color: 'rgba(255, 255, 255, 0.85)',
                    fontWeight: 400,
                    fontSize: '13px',
                  }}>
                    {area.prison_area_name}
                  </span>
                </div>

                <div className="progress-bar-container" style={{
                  flex: 1,
                  height: '10px',
                  background: 'rgba(255, 255, 255, 0.04)',
                  borderRadius: '5px',
                  overflow: 'hidden',
                  margin: '0 12px',
                  position: 'relative',
                }}>
                  <div style={{
                    height: '100%',
                    width: animated ? `${percentage}%` : '0%',
                    background: `linear-gradient(90deg, ${config.color}, ${config.color}dd)`,
                    borderRadius: '5px',
                    transition: `width 1s ease ${i * 0.1 + 0.3}s`,
                    boxShadow: `0 0 8px ${config.color}44`,
                    position: 'relative',
                  }}>
                    <div style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: '50%',
                      background: 'linear-gradient(180deg, rgba(255,255,255,0.25), transparent)',
                      borderRadius: '5px 5px 0 0',
                    }} />
                    {area.exit_count > 0 && (
                      <div className="shimmer" style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
                        borderRadius: '5px',
                        animation: `shimmer 2s ease-in-out ${i * 0.3}s infinite`,
                      }} />
                    )}
                  </div>
                </div>

                <div style={{
                  minWidth: '45px',
                  textAlign: 'right',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  gap: '4px',
                }}>
                  <AnimatedNumber
                    value={area.exit_count}
                    color={config.color}
                    delay={i * 100 + 300}
                  />
                  <span style={{
                    color: 'rgba(255, 255, 255, 0.4)',
                    fontSize: '11px',
                  }}>
                    人
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }

        @keyframes iconBreathe {
          0%, 100% {
            filter: drop-shadow(0 0 4px currentColor);
            opacity: 0.8;
          }
          50% {
            filter: drop-shadow(0 0 12px currentColor);
            opacity: 1;
          }
        }

        .exit-reason-row:hover .area-icon {
          animation: none !important;
          filter: drop-shadow(0 0 12px currentColor) !important;
          transform: scale(1.15);
          transition: all 0.2s ease;
        }

        .progress-bar-container:hover > div {
          box-shadow: 0 0 16px currentColor !important;
        }
      `}</style>
    </div>
  );
};

export default StatisticsChart;
