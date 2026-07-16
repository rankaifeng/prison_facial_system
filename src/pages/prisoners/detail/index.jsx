import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Row, Col, Tag, Button, Image } from 'antd';
import {
  ArrowLeftOutlined,
  UserOutlined,
  ManOutlined,
  WomanOutlined,
  LockOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { archive, record } from '@/api/globApi';
import TableLayout from '@/components/table-layout';
import VideoPlayer from '@/components/video-player';

const NO_IMG = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 50 50"><rect width="50" height="50" fill="#f0f0f0" rx="4"/><g transform="translate(25,22)"><circle r="8" fill="#bbb"/><path d="M-12,16 Q-12,8 0,8 Q12,8 12,16" fill="#bbb"/></g></svg>');

const PrisonerDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState(null);
  const [exitRecords, setExitRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [exitPagination, setExitPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  useEffect(() => {
    fetchDetail();
  }, [id]);

  const fetchDetail = async () => {
    setLoading(true);
    try {
      const [detailRes, exitRes] = await Promise.all([
        archive.detail({ prisoner_no: id }),
        record.list({ prisoner_no: id, type: 'exit', limit: 100 }),
      ]);

      if (detailRes?.code === 1 && detailRes?.data) {
        setDetail(detailRes.data);
      }

      const records = Array.isArray(exitRes) ? exitRes : [];
      setExitRecords(records);
      setExitPagination(prev => ({ ...prev, total: records.length }));
    } catch (error) {
      console.error('获取详情失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const exitColumns = [
    { title: '出监时间', dataIndex: 'exit_date', key: 'exit_date', width: 120 },
    { title: '出监原因', dataIndex: 'reason', key: 'reason', width: 120 },
    { title: '监区', dataIndex: 'prison_area_name', key: 'prison_area_name', width: 100 },
    {
      title: '民警确认',
      dataIndex: 'police_face',
      key: 'police_face',
      width: 100,
      render: (val) => val ? (
        <Image src={val} fallback={NO_IMG} style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover' }} />
      ) : (
        <Tag color="default">未录入</Tag>
      ),
    },
    {
      title: '民警姓名',
      dataIndex: 'police_name',
      key: 'police_name',
      width: 100,
    },
    {
      title: '特警确认',
      dataIndex: 'swat_face',
      key: 'swat_face',
      width: 100,
      render: (val) => val ? (
        <Image src={val} fallback={NO_IMG} style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover' }} />
      ) : (
        <Tag color="default">未录入</Tag>
      ),
    },{
      title: '特警姓名',
      dataIndex: 'swat_name',
      key: 'swat_name',
      width: 100,
    },{
      title: '武警确认',
      dataIndex: 'armed_police_signature',
      key: 'armed_police_signature',
      width: 100,
      render: (val) => val ? (
        <Image src={val} fallback={NO_IMG} style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover' }} />
      ) : (
        <Tag color="default">未录入</Tag>
      ),
    },
    { title: '出监时间', dataIndex: 'created_at', key: 'created_at', width: 120 },
    {
      title: '监控录像',
      dataIndex: 'video_url',
      key: 'video_url',
      width: 120,
      render: (_, record) => <VideoPlayer itemData={record} />,
    },
  ];

  const exitTableProps = useMemo(() => ({
    pagination: {
      current: exitPagination.current,
      pageSize: exitPagination.pageSize,
      total: exitPagination.total,
      showSizeChanger: true,
      showQuickJumper: true,
      onChange: (page, pageSize) => {
        setExitPagination({ current: page, pageSize, total: exitPagination.total });
      },
    },
    dataSource: exitRecords,
  }), [exitRecords, exitPagination]);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{
        marginBottom: 16,
        marginTop: 8,
        flexShrink: 0,
        backgroundColor: '#fff',
        borderRadius: 8,
        padding: '12px 16px',
        display: 'flex',
        alignItems: 'center',
      }}>
        <Button
          type="primary"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/prisoners')}
          style={{ borderRadius: 6 }}
        >
          返回列表
        </Button>
      </div>

      <Row gutter={[16, 16]} style={{ flex: 1, overflow: 'hidden', display: 'flex' }}>
        <Col xs={24} sm={24} md={24} lg={10} xl={8} style={{ height: '100%' }}>
          <Card
            loading={loading}
            className="profile-card"
            style={{ borderRadius: 12, height: '100%', overflow: 'auto' }}
            bodyStyle={{ padding: 0, height: '100%', overflow: 'auto' }}
          >
            <div className="profile-banner">
              <div className="banner-bg"></div>
              <div className="profile-content">
                <div className="profile-photo-large">
                  <img
                    src={detail?.mtxx?.[0]?.xp}
                    alt={detail?.xm || '照片'}
                  />
                </div>
                <h2 className="profile-title">{detail?.xm || '未知姓名'}</h2>
                <div className="profile-tags">
                  <Tag color={detail?.xb === '男' ? 'blue' : 'pink'} className="gender-tag">
                    {detail?.xb === '男' ? <ManOutlined /> : <WomanOutlined />}
                    {' '}{detail?.xb || '未知'}
                  </Tag>
                  <Tag color="gold" className="no-tag">{detail?.bh || '暂无编号'}</Tag>
                </div>
              </div>
            </div>

            <div className="profile-body">
              <div className="stats-row">
                <div className="stat-box">
                  <div className="stat-icon age-icon"><UserOutlined /></div>
                  <div className="stat-info">
                    <span className="stat-num">{detail?.age || '-'}</span>
                    <span className="stat-desc">年龄</span>
                  </div>
                </div>
                <div className="stat-box">
                  <div className="stat-icon sentence-icon"><LockOutlined /></div>
                  <div className="stat-info">
                    <span className="stat-num">{detail?.ypxq || '-'}</span>
                    <span className="stat-desc">刑期</span>
                  </div>
                </div>
                <div className="stat-box">
                  <div className="stat-icon ethnic-icon"><FileTextOutlined /></div>
                  <div className="stat-info">
                    <span className="stat-num">{detail?.mz || '-'}</span>
                    <span className="stat-desc">民族</span>
                  </div>
                </div>
              </div>

              <div className="info-group">
                <div className="info-group-title">
                  <LockOutlined />服刑信息
                </div>
                <div className="info-grid">
                  <div className="info-cell">
                    <span className="cell-label">罪名</span>
                    <span className="cell-value">{detail?.zm || '-'}</span>
                  </div>
                  <div className="info-cell">
                    <span className="cell-label">入监日期</span>
                    <span className="cell-value">{detail?.rjrq || '-'}</span>
                  </div>
                  <div className="info-cell">
                    <span className="cell-label">刑期止日</span>
                    <span className="cell-value highlight">{detail?.zr || '-'}</span>
                  </div>
                </div>
              </div>

              <div className="info-group">
                <div className="info-group-title">
                  <FileTextOutlined />基本信息
                </div>
                <div className="info-list">
                  <div className="info-row">
                    <span className="info-label">身份证号</span>
                    <span className="info-value mono">{detail?.sfzh || '-'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">婚姻状况</span>
                    <span className="info-value">{detail?.hy || '-'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">籍贯</span>
                    <span className="info-value">{detail?.jg || '-'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">户籍地址</span>
                    <span className="info-value">{detail?.hjzz || '-'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">家庭地址</span>
                    <span className="info-value">{detail?.jtmx || '-'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">文化程度</span>
                    <span className="info-value">{detail?.bqwhcd || '-'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">监区</span>
                    <span className="info-value">{detail?.db || '-'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">监室号/床号</span>
                    <span className="info-value">{detail?.jsh || '-'} / {detail?.cwh || '-'}</span>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={24} md={24} lg={14} xl={16} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <Card
            loading={loading}
            title={<span><FileTextOutlined />出监记录</span>}
            style={{ borderRadius: 12, flex: 1, display: 'flex', flexDirection: 'column' }}
            bodyStyle={{ flex: 1, overflow: 'hidden', padding: 0 }}
          >
            <TableLayout
              tableProps={exitTableProps}
              loading={loading}
              columns={exitColumns}
            />
          </Card>
        </Col>
      </Row>

      <style>{`
        .profile-card {
          border: none !important;
          box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08) !important;
        }

        .profile-banner {
          position: relative;
          padding: 40px 20px 30px;
          text-align: center;
        }

        .banner-bg {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 100px;
          background: linear-gradient(135deg, #3b7dd8 0%, #722ed1 50%, #eb2f96 100%);
          border-radius: 12px 12px 0 0;
        }

        .profile-content {
          position: relative;
          z-index: 1;
        }

        .profile-photo-large {
          width: 100px;
          height: 130px;
          margin: 0 auto 16px;
          border-radius: 12px;
          overflow: visible;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
          border: 4px solid #fff;
          position: relative;
          z-index: 2;
        }

        .profile-photo-large img {
          width: 100%;
          height: 130px;
          object-fit: cover;
          border-radius: 8px;
        }

        .profile-title {
          margin: 0 0 12px 0 !important;
          font-size: 22px !important;
          font-weight: 700 !important;
          color: #333;
        }

        .profile-tags {
          display: flex;
          justify-content: center;
          gap: 8px;
        }

        .profile-tags .ant-tag {
          border-radius: 4px;
          padding: 2px 10px;
          font-size: 13px;
        }

        .gender-tag {
          background: rgba(24, 144, 255, 0.1) !important;
        }

        .no-tag {
          background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%) !important;
          color: #fff !important;
          border: none !important;
        }

        .profile-body {
          padding: 20px;
        }

        .stats-row {
          display: flex;
          gap: 12px;
          margin-bottom: 20px;
        }

        .stat-box {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 14px 12px;
          background: linear-gradient(135deg, #f0f5ff 0%, #e6f0ff 100%);
          border-radius: 10px;
          border: 1px solid #e6f0ff;
        }

        .stat-icon {
          width: 40px;
          height: 40px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
        }

        .age-icon {
          background: linear-gradient(135deg, #3b7dd8 0%, #40a9ff 100%);
          color: #fff;
        }

        .sentence-icon {
          background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);
          color: #fff;
        }

        .ethnic-icon {
          background: linear-gradient(135deg, #fa8c16 0%, #ffb732 100%);
          color: #fff;
        }

        .stat-info {
          display: flex;
          flex-direction: column;
        }

        .stat-num {
          font-size: 15px;
          font-weight: 700;
          color: #333;
          line-height: 1.3;
        }

        .stat-desc {
          font-size: 11px;
          color: #999;
        }

        .info-group {
          margin-bottom: 20px;
        }

        .info-group-title {
          font-size: 14px;
          font-weight: 600;
          color: #333;
          margin-bottom: 12px;
          padding-bottom: 8px;
          border-bottom: 2px solid #3b7dd8;
          display: inline-block;
        }

        .info-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
        }

        .info-cell {
          background: #fafafa;
          padding: 12px;
          border-radius: 8px;
          text-align: center;
        }

        .cell-label {
          display: block;
          font-size: 11px;
          color: #999;
          margin-bottom: 4px;
        }

        .cell-value {
          display: block;
          font-size: 13px;
          font-weight: 600;
          color: #333;
        }

        .cell-value.highlight {
          color: #3b7dd8;
        }

        .info-list {
          background: #fafafa;
          border-radius: 10px;
          padding: 4px 0;
        }

        .info-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 10px 14px;
          border-bottom: 1px solid #f0f0f0;
        }

        .info-row:last-child {
          border-bottom: none;
        }

        .info-label {
          font-size: 13px;
          color: #666;
        }

        .info-value {
          font-size: 13px;
          font-weight: 500;
          color: #333;
          max-width: 60%;
          text-align: right;
          word-break: break-all;
        }

        .info-value.mono {
          font-family: 'Courier New', monospace;
          font-size: 12px;
        }

        .ant-card-head {
          min-height: 44px;
          padding: 0 16px;
          border-bottom: 1px solid #f0f0f0;
        }

        .ant-card-head-title {
          font-size: 15px;
          font-weight: 600;
        }

        .ant-card-body {
          padding: 0;
          height: 100%;
          display: flex;
          flex-direction: column;
        }
      `}</style>
    </div>
  );
};

export default PrisonerDetail;
