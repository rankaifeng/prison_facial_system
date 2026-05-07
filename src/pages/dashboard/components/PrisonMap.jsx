import React, { useEffect, useState } from 'react';
import './PrisonMap.css';

const PrisonMap = ({ prisons = [] }) => {
  const [data, setData] = useState([]);
  const [hoveredIndex, setHoveredIndex] = useState(null);

  useEffect(() => {
    if (prisons.length > 0) {
      setData(prisons.slice(0, 7));
    } else {
      setData([
        { name: '第一监狱', totalCount: 456, workCount: 320 },
        { name: '第二监狱', totalCount: 382, workCount: 285 },
        { name: '第三监狱', totalCount: 520, workCount: 410 },
        { name: '第四监狱', totalCount: 298, workCount: 220 },
        { name: '第五监狱', totalCount: 445, workCount: 360 },
        { name: '第六监狱', totalCount: 510, workCount: 395 },
        { name: '第七监狱', totalCount: 389, workCount: 298 },
      ]);
    }
  }, [prisons]);

  return (
    <div className="prison-map-container">
      <div className="china-map">
        <div className="map-region region-nw" onMouseEnter={() => setHoveredIndex(0)} onMouseLeave={() => setHoveredIndex(null)}>
          <div className="region-inner">
            <div className="region-name">{data[0]?.name}</div>
            <div className="region-stats">
              <div className="stat"><span className="label">总</span><span className="value">{data[0]?.totalCount}</span></div>
              <div className="stat highlight"><span className="label">出</span><span className="value">{data[0]?.workCount}</span></div>
            </div>
          </div>
          {hoveredIndex === 0 && <div className="region-glow"></div>}
        </div>
        <div className="map-region region-ne" onMouseEnter={() => setHoveredIndex(1)} onMouseLeave={() => setHoveredIndex(null)}>
          <div className="region-inner">
            <div className="region-name">{data[1]?.name}</div>
            <div className="region-stats">
              <div className="stat"><span className="label">总</span><span className="value">{data[1]?.totalCount}</span></div>
              <div className="stat highlight"><span className="label">出</span><span className="value">{data[1]?.workCount}</span></div>
            </div>
          </div>
          {hoveredIndex === 1 && <div className="region-glow"></div>}
        </div>
        <div className="map-region region-hb" onMouseEnter={() => setHoveredIndex(2)} onMouseLeave={() => setHoveredIndex(null)}>
          <div className="region-inner">
            <div className="region-name">{data[2]?.name}</div>
            <div className="region-stats">
              <div className="stat"><span className="label">总</span><span className="value">{data[2]?.totalCount}</span></div>
              <div className="stat highlight"><span className="label">出</span><span className="value">{data[2]?.workCount}</span></div>
            </div>
          </div>
          {hoveredIndex === 2 && <div className="region-glow"></div>}
        </div>
        <div className="map-region region-hn" onMouseEnter={() => setHoveredIndex(3)} onMouseLeave={() => setHoveredIndex(null)}>
          <div className="region-inner">
            <div className="region-name">{data[3]?.name}</div>
            <div className="region-stats">
              <div className="stat"><span className="label">总</span><span className="value">{data[3]?.totalCount}</span></div>
              <div className="stat highlight"><span className="label">出</span><span className="value">{data[3]?.workCount}</span></div>
            </div>
          </div>
          {hoveredIndex === 3 && <div className="region-glow"></div>}
        </div>
        <div className="map-region region-xb" onMouseEnter={() => setHoveredIndex(4)} onMouseLeave={() => setHoveredIndex(null)}>
          <div className="region-inner">
            <div className="region-name">{data[4]?.name}</div>
            <div className="region-stats">
              <div className="stat"><span className="label">总</span><span className="value">{data[4]?.totalCount}</span></div>
              <div className="stat highlight"><span className="label">出</span><span className="value">{data[4]?.workCount}</span></div>
            </div>
          </div>
          {hoveredIndex === 4 && <div className="region-glow"></div>}
        </div>
        <div className="map-region region-db" onMouseEnter={() => setHoveredIndex(5)} onMouseLeave={() => setHoveredIndex(null)}>
          <div className="region-inner">
            <div className="region-name">{data[5]?.name}</div>
            <div className="region-stats">
              <div className="stat"><span className="label">总</span><span className="value">{data[5]?.totalCount}</span></div>
              <div className="stat highlight"><span className="label">出</span><span className="value">{data[5]?.workCount}</span></div>
            </div>
          </div>
          {hoveredIndex === 5 && <div className="region-glow"></div>}
        </div>
        <div className="map-region region-nn" onMouseEnter={() => setHoveredIndex(6)} onMouseLeave={() => setHoveredIndex(null)}>
          <div className="region-inner">
            <div className="region-name">{data[6]?.name}</div>
            <div className="region-stats">
              <div className="stat"><span className="label">总</span><span className="value">{data[6]?.totalCount}</span></div>
              <div className="stat highlight"><span className="label">出</span><span className="value">{data[6]?.workCount}</span></div>
            </div>
          </div>
          {hoveredIndex === 6 && <div className="region-glow"></div>}
        </div>
      </div>
    </div>
  );
};

export default PrisonMap;