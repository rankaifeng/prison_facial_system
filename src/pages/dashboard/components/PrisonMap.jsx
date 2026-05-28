import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import * as echarts from 'echarts';
//center: [114, 23], { name: '分监区六', province: '广东', code: '440000', coordinates: [113.26, 23.13], totalCount: 510, workCount: 395 },

//用户表 档案表 出入记录表
const PrisonMap = ({ realtimeData, isAdmin }) => {
  const chartRef = useRef(null);
  const navigate = useNavigate();

  // 从API获取的 by_area 数据
  const byArea = realtimeData?.by_area || [];

  // 获取当前登录的监区名称
  const getStoredPrisonName = () => {
    try {
      const stored = localStorage.getItem('prisonName');
      return stored || '';
    } catch {
      return '';
    }
  };

  const currentPrisonName = getStoredPrisonName();

  const mCont = [
    { name: '监区一', province: '四川', code: '510000', coordinates: [104.06, 30.67], totalCount: 0, yearlyExitCount: 0 },
    { name: '监区二', province: '云南', code: '530000', coordinates: [101.34, 25.04], totalCount: 0, yearlyExitCount: 0 },
    { name: '监区三', province: '贵州', code: '520000', coordinates: [106.71, 26.60], totalCount: 0, yearlyExitCount: 0 },
    { name: '监区四', province: '广西', code: '450000', coordinates: [108.33, 22.84], totalCount: 0, yearlyExitCount: 0 },
    { name: '监区五', province: '湖南', code: '430000', coordinates: [112.94, 28.24], totalCount: 0, yearlyExitCount: 0 },
    { name: '监区六', province: '广东', code: '440000', coordinates: [113.26, 23.13], totalCount: 0, yearlyExitCount: 0 },
    { name: '监区七', province: '江西', code: '360000', coordinates: [115.89, 28.68], totalCount: 0, yearlyExitCount: 0 },
    { name: '备用监区', province: '重庆', code: '500000', coordinates: [106.55, 29.56], totalCount: 0, yearlyExitCount: 0 },
  ];

  // 非管理员只显示登录的监区
  const displayCont = isAdmin
    ? mCont
    : (mCont.filter(item => item.name === currentPrisonName)[0] ? mCont.filter(item => item.name === currentPrisonName) : [mCont[0]]);

  useEffect(() => {
    const chart = echarts.init(chartRef.current);

    const updatedCont = displayCont.map((item) => {
      const area = byArea.find(a => a.prison_area_name === item.name);
      return {
        ...item,
        totalCount: 22 || 0,
        yearlyExitCount: area?.yearly_exit_count || 0,
      };
    });

      fetch('/china.json')
      .then(res => res.json())
      .then(chinaData => {
        const provinces = updatedCont.map(p => p.code);

        const filteredFeatures = chinaData.features.filter(feature => {
          const adcode = feature.properties.adcode || feature.properties.id;
          return provinces.includes(String(adcode));
        });

        const mapData = {
          type: 'FeatureCollection',
          features: filteredFeatures
        };

        echarts.registerMap('prison-map', mapData);

        const provinceCenters = {};
        filteredFeatures.forEach(feature => {
          const name = feature.properties.name;
          const coords = feature.geometry.coordinates;
          let allCoords = [];
          if (feature.geometry.type === 'Polygon') {
            allCoords = coords[0];
          } else if (feature.geometry.type === 'MultiPolygon') {
            coords.forEach(p => allCoords = allCoords.concat(p[0]));
          }
          if (allCoords.length > 0) {
            const sumX = allCoords.reduce((sum, c) => sum + c[0], 0);
            const sumY = allCoords.reduce((sum, c) => sum + c[1], 0);
            provinceCenters[name] = [sumX / allCoords.length, sumY / allCoords.length];
          }
        });

        const finalCont = updatedCont.map(p => {
          const center = provinceCenters[p.province + '省'] || provinceCenters[p.province + '市'] || provinceCenters[p.province + '自治区'] || provinceCenters[p.province];
          return {
            ...p,
            coordinates: center || p.coordinates,
          };
        });

        // 非管理员使用监区预设坐标并放大
        const displayCenter = isAdmin
          ? [108, 27]
          : (updatedCont[0]?.coordinates || [108, 27]);
        const displayZoom = isAdmin ? 1.2 : 1.1;

        const option = {
          backgroundColor: 'transparent',
          tooltip: {
            show: false,
          },
          geo: {
            map: 'prison-map',
            roam: true,
            scaleLimit: { min: 0.5, max: 3 },
            zoom: displayZoom,
            center: displayCenter,
            aspectScale: 1,
            label: { show: false },
            itemStyle: {
              areaColor: 'rgba(30, 40, 70, 0.8)',
              borderColor: 'rgba(0, 240, 255, 0.4)',
              borderWidth: 1,
            },
            emphasis: {
              itemStyle: {
                areaColor: 'rgba(0, 240, 255, 0.3)',
                borderColor: 'rgba(0, 240, 255, 0.8)',
                borderWidth: 2,
              },
              label: { show: false },
            },
          },
          series: [
            {
              name: '监狱',
              type: 'effectScatter',
              coordinateSystem: 'geo',
              data: finalCont.map(p => {
                return {
                  name: p.name,
                  value: [...p.coordinates, p.totalCount],
                  totalCount: p.totalCount,
                  yearlyExitCount: p.yearlyExitCount,
                }
              }),
              symbolSize: (val) => {
                const count = val[2];
                return Math.max(15, Math.min(30, count / 20));
              },
              showEffectOn: 'render',
              rippleEffect: {
                period: 2,
                scale: 2.5,
                brushType: 'fill',
                color: '#00f0ff',
              },
              itemStyle: {
                color: {
                  type: 'radial',
                  x: 0.5, y: 0.5, r: 0.5,
                  colorStops: [
                    { offset: 0, color: '#00f0ff' },
                    { offset: 0.5, color: 'rgba(0, 240, 255, 0.8)' },
                    { offset: 1, color: 'rgba(0, 200, 255, 0.4)' },
                  ],
                },
                shadowBlur: 15,
                shadowColor: 'rgba(0, 240, 255, 0.5)',
              },
              label: {
                show: true,
                position: 'top',
                formatter: (params) => `📍 ${params.data.name}\n👥 实时在监人数: ${params.data.totalCount}\n🚶 当年累计出监人数: ${params.data.yearlyExitCount}`,
                fontSize: 11,
                color: '#fff',
                backgroundColor: 'rgba(20, 25, 45, 0.9)',
                padding: [6, 10],
                borderRadius: 4,
                borderColor: 'rgba(0, 240, 255, 0.3)',
                distance: 10,
              },
              emphasis: { scale: 1.3 },
            },
          ],
        };

        chart.setOption(option);

        chart.on('click', (params) => {
          if (params.seriesType === 'effectScatter' && params.name) {
            navigate(`/statistics?prisonName=${encodeURIComponent(params.name)}`);
          }
        });
      })
      .catch(err => console.error('Failed to load map:', err));

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [realtimeData, isAdmin, currentPrisonName]);

  return <div ref={chartRef} style={{ width: '100%', height: '100%' }} />;
};

export default PrisonMap;