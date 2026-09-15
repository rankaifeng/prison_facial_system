import React from 'react';
import { useNavigate } from 'react-router-dom';
import bgImg from '@/imgs/bg.png';
import './PrisonMap.css';

// 8 栋楼在 bg.png 上的屋顶中心（百分比，已按网格在原图上标定）
// leader: 从楼中心圆点向上的竖线长度（设计稿 px），八监区加长避免与二监区卡片重叠
const AREA_POSITIONS = [
  // { name: '八监区', x: 44.0, y: 9.0, leader: 56 },
  { name: '二监区', x: 58.5, y: 16.5, leader: 20 },
  { name: '三监区', x: 87.5, y: 22.0, leader: 20 },
  { name: '四监区', x: 45.5, y: 33.5, leader: 20 },
  { name: '五监区', x: 25.0, y: 47.5, leader: 20 },
  { name: '六监区', x: 71.5, y: 46.5, leader: 20 },
  { name: '七监区', x: 46.0, y: 65.0, leader: 20 },
  { name: '一监区', x: 69.0, y: 76.5, leader: 20 },
];

// 设计稿基准宽度：卡片/引线尺寸按此宽度换算成容器查询单位（cqw），
// 图片以百分比铺满容器、标注按百分比定位，因此任何屏幕下构图一致、四边铺满
const DESIGN_WIDTH = 1074;
const cqw = px => `calc(${px} * 100cqw / ${DESIGN_WIDTH})`;
const DEFAULT_LEADER = 20;

//用户表 档案表 出入记录表
const PrisonMap = ({ realtimeData, isAdmin }) => {
  const navigate = useNavigate();

  // 从API获取的 by_area 数据
  const byArea = realtimeData?.by_area;

  // 获取当前登录的监区名称
  const getStoredPrisonName = () => {
    try {
      return localStorage.getItem('prisonName') || '';
    } catch {
      return '';
    }
  };

  const currentPrisonName = getStoredPrisonName();

  // 非管理员只显示登录的监区，匹配不到时回退一监区
  const displayAreas = isAdmin
    ? AREA_POSITIONS
    : AREA_POSITIONS.filter(item => item.name === currentPrisonName);
  const areas = displayAreas.length > 0 ? displayAreas : [AREA_POSITIONS[0]];

  const markers = areas.map((item) => {
    const area = (byArea || []).find(a => a.prison_area_name === item.name);
    return {
      ...item,
      inPrisonCount: area?.in_prison_count ?? 0,
      entryCount: area?.entry_count ?? 0,
      exitCount: area?.exit_count ?? 0,
      yearlyExitCount: area?.yearly_exit_count ?? 0,
    };
  });

  const handleClick = (name) => {
    navigate(`/statistics?prisonName=${encodeURIComponent(name)}`);
  };

  return (
    <div className="prison-map">
      <div className="map-image" style={{ backgroundImage: `url(${bgImg})` }} />
      <div className="map-markers">
        {markers.map(m => {
          const leader = m.leader || DEFAULT_LEADER;
          return (
            <div
              key={m.name}
              className="prison-area-marker"
              style={{ left: `${m.x}%`, top: `${m.y}%` }}
              title={`${m.name} 出入统计`}
              onClick={() => handleClick(m.name)}
            >
              <span className="anchor-dot" />
              <span className="leader-line" style={{ height: cqw(leader) }} />
              <div className="area-card" style={{ bottom: cqw(leader) }}>
                <div className="area-name">{m.name}</div>
                <div className="area-stats">
                  <span className="stat-item">实时在监人数： <b className="num-amber">{m.inPrisonCount}</b></span>
                </div>
                <div className="area-stats">
                  <span className="stat-item">当年累计出监人数： <b className="num-amber">{m.yearlyExitCount}</b></span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PrisonMap;
