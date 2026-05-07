import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

const PrisonMap = () => {
  const chartRef = useRef(null);

  const prisons = [
    { name: '第一监狱', province: '四川', code: '510000', coordinates: [104.06, 30.67], totalCount: 456, workCount: 320 },
    { name: '第二监狱', province: '云南', code: '530000', coordinates: [101.34, 25.04], totalCount: 382, workCount: 285 },
    { name: '第三监狱', province: '贵州', code: '520000', coordinates: [106.71, 26.60], totalCount: 520, workCount: 410 },
    { name: '第四监狱', province: '广西', code: '450000', coordinates: [108.33, 22.84], totalCount: 298, workCount: 220 },
    { name: '第五监狱', province: '湖南', code: '430000', coordinates: [112.94, 28.24], totalCount: 445, workCount: 360 },
    { name: '第六监狱', province: '广东', code: '440000', coordinates: [113.26, 23.13], totalCount: 510, workCount: 395 },
    { name: '第七监狱', province: '江西', code: '360000', coordinates: [115.89, 28.68], totalCount: 389, workCount: 298 },
  ];

  useEffect(() => {
    const chart = echarts.init(chartRef.current);

    fetch('/china.json')
      .then(res => res.json())
      .then(chinaData => {
        const provinces = prisons.map(p => p.code);

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

        prisons.forEach(p => {
          const center = provinceCenters[p.province + '省'] || provinceCenters[p.province];
          if (center) {
            p.coordinates = center;
          }
        });

        const option = {
          backgroundColor: 'transparent',
          tooltip: {
            show: false,
          },
          geo: {
            map: 'prison-map',
            roam: true,
            scaleLimit: { min: 0.5, max: 3 },
            zoom: 1.2,
            center: [108, 27],
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
              data: prisons.map(p => ({
                name: p.name,
                value: [...p.coordinates, p.totalCount],
                totalCount: p.totalCount,
                workCount: p.workCount,
              })),
              symbolSize: (val) => {
                const count = val[2];
                return Math.max(15, Math.min(30, count / 20));
              },
              showEffectOn: 'render',
              rippleEffect: {
                period: 2,
                scale: 2.5,
                brushType: 'stroke',
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
                formatter: (params) => `${params.data.name}\n总人数: ${params.data.totalCount}\n出监人数: ${params.data.workCount}`,
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
      })
      .catch(err => console.error('Failed to load map:', err));

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, []);

  return <div ref={chartRef} style={{ width: '100%', height: '100%' }} />;
};

export default PrisonMap;