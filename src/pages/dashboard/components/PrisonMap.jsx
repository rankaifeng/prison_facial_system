import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import bgImg from '@/imgs/bg.png';
import './PrisonMap.css';

// 8 栋楼在 bg.png 上的楼顶锚点（百分比坐标，已按图片实际位置标定）
// leader: 从楼中间向左引出的标注线长度（px），上下相邻的卡片用不同长度错开
const AREA_POSITIONS = [
  { name: '八监区', x: 47.2, y: 11.5, leader: 110 },
  { name: '二监区', x: 62.0, y: 20.5, leader: 40 },
  { name: '三监区', x: 89.5, y: 25.5, leader: 40 },
  { name: '四监区', x: 48.3, y: 37.5, leader: 40 },
  { name: '五监区', x: 27.8, y: 51.5, leader: 40 },
  { name: '六监区', x: 75.5, y: 50.5, leader: 40 },
  { name: '七监区', x: 48.6, y: 68.5, leader: 40 },
  { name: '一监区', x: 72.8, y: 77.5, leader: 40 },
];

const IMAGE_RATIO = 2752 / 1536;
const DEFAULT_LEADER = 40;
const EDGE_PAD = 12;

//用户表 档案表 出入记录表
const PrisonMap = ({ realtimeData, isAdmin }) => {
  const wrapRef = useRef(null);
  const stageRef = useRef(null);
  const navigate = useNavigate();
  const [stageBox, setStageBox] = useState({ width: 0, height: 0, left: 0, top: 0 });

  // 从API获取的 by_area 数据（保持引用稳定，避免 || [] 每次生成新数组导致 effect 死循环）
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

  // 数字变化会改变卡片文字宽度，用原始值字符串作为重测依赖
  const measureKey = markers.map(m => `${m.inPrisonCount}/${m.yearlyExitCount}`).join('|');

  // 容器尺寸变化时按图片比例计算舞台大小（cover 铺满）
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const update = () => {
      const w = el.clientWidth;
      const h = el.clientHeight;
      // cover：图片铺满容器，超出部分裁掉；标注跟随内层舞台定位，不会错位
      let sw = w;
      let sh = w / IMAGE_RATIO;
      if (sh < h) {
        sh = h;
        sw = h * IMAGE_RATIO;
      }
      setStageBox(prev => ({ ...prev, width: sw, height: sh }));
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // 实测所有标注卡片的真实包围盒，平移舞台让卡片完整落在容器内
  // （引线锚点允许随 cover 裁到画面外，线从画面边缘自然伸入）
  useLayoutEffect(() => {
    const wrap = wrapRef.current;
    const stage = stageRef.current;
    if (!wrap || !stage || !stageBox.width) return;
    const cw = wrap.clientWidth;
    const ch = wrap.clientHeight;
    const sr = stage.getBoundingClientRect();
    let minL = Infinity;
    let minT = Infinity;
    let maxR = -Infinity;
    let maxB = -Infinity;
    stage.querySelectorAll('.area-card').forEach(card => {
      const r = card.getBoundingClientRect();
      minL = Math.min(minL, r.left - sr.left);
      maxR = Math.max(maxR, r.right - sr.left);
      minT = Math.min(minT, r.top - sr.top);
      maxB = Math.max(maxB, r.bottom - sr.top);
    });
    if (!isFinite(minL)) return;
    const calcOffset = (min, max, container, size) => {
      if (size <= container) return (container - size) / 2;
      const lo = EDGE_PAD - min;
      const hi = container - EDGE_PAD - max;
      if (lo > hi) return container / 2 - (min + max) / 2; // 放不下时让卡片包围盒居中
      return Math.min(Math.max((container - size) / 2, lo), hi);
    };
    setStageBox(prev => {
      const left = calcOffset(minL, maxR, cw, prev.width);
      const top = calcOffset(minT, maxB, ch, prev.height);
      // 亚像素收敛：变化小于 0.5px 不再更新，避免反复重排
      if (Math.abs(left - prev.left) < 0.5 && Math.abs(top - prev.top) < 0.5) {
        return prev;
      }
      return { ...prev, left, top };
    });
  }, [stageBox.width, stageBox.height, isAdmin, currentPrisonName, measureKey]);

  const handleClick = (name) => {
    navigate(`/statistics?prisonName=${encodeURIComponent(name)}`);
  };

  return (
    <div className="prison-map" ref={wrapRef}>
      <div
        ref={stageRef}
        className="prison-map-stage"
        style={{
          width: stageBox.width,
          height: stageBox.height,
          left: stageBox.left,
          top: stageBox.top,
          backgroundImage: `url(${bgImg})`,
        }}
      >
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
              <span className="leader-line" style={{ width: leader }} />
              <div className="area-card" style={{ right: leader }}>
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
