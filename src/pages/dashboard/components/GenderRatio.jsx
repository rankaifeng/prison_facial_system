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

      <div className="gender-row">
        <div className="gender-side male-side">
          <div className="icon-col">
            <ManOutlined className="gender-icon" />
            <div className="gender-label">男性</div>
          </div>
          <div className="count-col">
            <div className="gender-count">{maleCount}</div>
            <div className="gender-percent">{malePercent}%</div>
          </div>
        </div>

        <div className="gender-ring-wrapper">
          <svg viewBox="0 0 100 100" className="ring-svg">
            {/* 3D效果底层阴影 */}
            <circle
              cx="50"
              cy="52"
              r="40"
              fill="none"
              stroke="rgba(0, 0, 0, 0.3)"
              strokeWidth="12"
            />
            {/* 底层背景 */}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="rgba(24, 119, 255, 0.1)"
              strokeWidth="12"
            />
            {/* 男性3D外圈 */}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="rgba(0, 200, 255, 0.4)"
              strokeWidth="14"
              strokeLinecap="round"
              strokeDasharray={`${malePercent * 2.51} 251`}
              transform="rotate(-90 50 50)"
              className="ring-progress male-ring outer-ring"
            />
            {/* 男性内圈 */}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="url(#maleGradient)"
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={`${malePercent * 2.51} 251`}
              transform="rotate(-90 50 50)"
              className="ring-progress male-ring"
            />
            {/* 女性3D外圈 */}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="rgba(255, 100, 100, 0.4)"
              strokeWidth="14"
              strokeLinecap="round"
              strokeDasharray={`${femalePercent * 2.51} 251`}
              strokeDashoffset={`-${malePercent * 2.51}`}
              transform="rotate(-90 50 50)"
              className="ring-progress female-ring outer-ring"
            />
            {/* 女性内圈 */}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="url(#femaleGradient)"
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={`${femalePercent * 2.51} 251`}
              strokeDashoffset={`-${malePercent * 2.51}`}
              transform="rotate(-90 50 50)"
              className="ring-progress female-ring"
            />
            <defs>
              <linearGradient id="maleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#00f0ff" />
                <stop offset="50%" stopColor="#1890ff" />
                <stop offset="100%" stopColor="#0030aa" />
              </linearGradient>
              <linearGradient id="femaleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ff8a8a" />
                <stop offset="50%" stopColor="#ff4d4f" />
                <stop offset="100%" stopColor="#aa0020" />
              </linearGradient>
            </defs>
          </svg>
          <div className="ring-center">
            <div className="ring-total">{total}</div>
          </div>
        </div>

        <div className="gender-side female-side">
          <div className="count-col">
            <div className="gender-count">{femaleCount}</div>
            <div className="gender-percent">{femalePercent}%</div>
          </div>
          <div className="icon-col">
            <WomanOutlined className="gender-icon" />
            <div className="gender-label">女性</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GenderRatio;
