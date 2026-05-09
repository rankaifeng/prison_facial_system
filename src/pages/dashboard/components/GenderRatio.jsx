import React from 'react';
import { ManOutlined, WomanOutlined } from '@ant-design/icons';

const GenderRatio = ({ maleCount = 680, femaleCount = 210 }) => {
  const total = maleCount + femaleCount;
  const malePercent = total > 0 ? ((maleCount / total) * 100).toFixed(1) : 0;
  const femalePercent = total > 0 ? ((femaleCount / total) * 100).toFixed(1) : 0;

  return (
    <div className="gender-ratio-section">
      <div className="section-header">
        <span>性别比例分析</span>
      </div>

      <div className="gender-cards">
        <div className="gender-card male">
          <div className="gender-icon-wrapper">
            <ManOutlined />
          </div>
          <div className="gender-info">
            <div className="gender-label">男性</div>
            <div className="gender-count">{maleCount}</div>
            <div className="gender-percent">{malePercent}%</div>
          </div>
          <div className="gender-bar">
            <div
              className="gender-bar-fill male-bar"
              style={{ width: `${malePercent}%` }}
            />
          </div>
        </div>

        <div className="gender-card female">
          <div className="gender-icon-wrapper">
            <WomanOutlined />
          </div>
          <div className="gender-info">
            <div className="gender-label">女性</div>
            <div className="gender-count">{femaleCount}</div>
            <div className="gender-percent">{femalePercent}%</div>
          </div>
          <div className="gender-bar">
            <div
              className="gender-bar-fill female-bar"
              style={{ width: `${femalePercent}%` }}
            />
          </div>
        </div>
      </div>

      <div className="gender-summary">
        <div className="summary-ring">
          <svg viewBox="0 0 100 100" className="ring-svg">
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="rgba(24, 119, 255, 0.2)"
              strokeWidth="12"
            />
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="url(#maleGradient)"
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={`${malePercent * 2.51} 251`}
              transform="rotate(-90 50 50)"
              className="ring-progress"
            />
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="url(#femaleGradient)"
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={`${femalePercent * 2.51} 251`}
              strokeDashoffset={`-${malePercent * 2.51}`}
              transform="rotate(-90 50 50)"
              className="ring-progress"
            />
            <defs>
              <linearGradient id="maleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#1890ff" />
                <stop offset="100%" stopColor="#00f0ff" />
              </linearGradient>
              <linearGradient id="femaleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ff4d4f" />
                <stop offset="100%" stopColor="#ff8a8a" />
              </linearGradient>
            </defs>
          </svg>
          <div className="ring-center">
            <div className="ring-total">{total}</div>
            <div className="ring-label">总计</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GenderRatio;
