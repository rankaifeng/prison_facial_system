import React from 'react';
import { UserOutlined, HeartOutlined, MedicineBoxOutlined, LockOutlined, DisconnectOutlined, HomeOutlined, ThunderboltOutlined, ArrowUpOutlined } from '@ant-design/icons';
import GenderRatio from './GenderRatio';

const LeftPanel = ({ realtimeData }) => {
  // 实时在监总人数 - 来自API的 total.in_prison_count
  const total = realtimeData?.total?.in_prison_count || 0;

  // 各出监原因数量 - 来自API的 total.reasons
  const reasons = realtimeData?.total?.reasons || [];

  // 计算各原因的数量
  const getReasonCount = (reasonName) => {
    const reason = reasons.find(r => r.name === reasonName);
    return reason ? reason.count : 0;
  };

  return (
    <div className="left-panel">
      <div className="panel-section total-section">
        <div className="chart-header">
          <div className="header-content">
            <UserOutlined />
            <span>实时在监总人数</span>
          </div>
          <div className="header-line"></div>
          <div className="header-decor">
            <span className="decor-dot"></span>
            <span className="decor-dot"></span>
            <span className="decor-dot"></span>
          </div>
        </div>
        <div className="total-display">
          <div className="total-circle" style={{ marginTop: 20 }}>
            <div className="total-value">{total}</div>
            <div className="total-unit">人</div>
          </div>
          <div className="total-decoration">
            <div className="decoration-line"></div>
            <div className="decoration-dot"></div>
          </div>
        </div>
      </div>

      {/* <GenderRatio
        maleCount={genderData?.male || 680}
        femaleCount={genderData?.female || 210}
      /> */}

      <div className="panel-section stats-section">
        <div className="section-header">
          <div className="header-content">
            <LockOutlined />
            <span>监狱罪犯情况</span>
          </div>
          <div className="header-line"></div>
          <div className="header-decor">
            <span className="decor-dot"></span>
            <span className="decor-dot"></span>
            <span className="decor-dot"></span>
          </div>
          <div className="header-stat">
            <span>当天出监总人数：{realtimeData?.total?.exit_count || 0}</span>
          </div>
        </div>
        <div className="stats-grid">
          <div className="stat-box">
            <div className="stat-icon in-prison">
              <UserOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">刑满释放</div>
              <div className="stat-number">{getReasonCount('刑满释放')}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon working">
              <ThunderboltOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">外出就医</div>
              <div className="stat-number">{getReasonCount('外出就医')}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon hospital">
              <MedicineBoxOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">外出教育</div>
              <div className="stat-number">{getReasonCount('外出教育')}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon isolated">
              <LockOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">离监探亲</div>
              <div className="stat-number">{getReasonCount('离监探亲')}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon quarantine">
              <DisconnectOutlined />
            </div>
            <div className="stat-content">
              <div className="stat-label">押回重审</div>
              <div className="stat-number">{getReasonCount('押回重审')}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeftPanel;