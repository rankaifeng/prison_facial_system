import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Row, Col, Tag, Button } from 'antd';
import {
  ArrowLeftOutlined,
  UserOutlined,
  ManOutlined,
  WomanOutlined,
  CalendarOutlined,
  FileTextOutlined,
  LockOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons';
import { prisoner, exitRecord } from '@/api/globApi';
import TableLayout from '@/components/table-layout';

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
      const [detailData, exitData] = await Promise.all([
        prisoner.detail({ id }),
        exitRecord.list({ prisonerId: id }),
      ]);
      setDetail(detailData?.data || {});
      const records = Array.isArray(exitData) ? exitData : [];
      setExitRecords(records);
      setExitPagination(prev => ({ ...prev, total: records.length }));
    } catch (error) {
      console.error('获取详情失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const exitColumns = [
    { title: '出监时间', dataIndex: 'exitTime', key: 'exitTime', width: 160 },
    { title: '出监原因', dataIndex: 'exitReason', key: 'exitReason', width: 120 },
    { title: '就医医院', dataIndex: 'hospital', key: 'hospital', width: 150 },
    {
      title: '民警确认',
      dataIndex: 'policeConfirm',
      key: 'policeConfirm',
      width: 100,
      render: (val) => val ? (
        <img src="/imgs/face.png" alt="已确认" style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover' }} />
      ) : (
        <img src="/imgs/face.png" alt="未确认" style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover', opacity: 0.4 }} />
      ),
    },
    {
      title: '特警确认',
      dataIndex: 'swatConfirm',
      key: 'swatConfirm',
      width: 100,
      render: (val) => val ? (
        <img src="/imgs/face.png" alt="已确认" style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover' }} />
      ) : (
        <img src="/imgs/face.png" alt="未确认" style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover', opacity: 0.4 }} />
      ),
    },
    {
      title: '武警确认',
      dataIndex: 'armedPoliceConfirm',
      key: 'armedPoliceConfirm',
      width: 100,
      render: (val) => val ? (
        <img src="/imgs/face.png" alt="已确认" style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover' }} />
      ) : (
        <img src="/imgs/face.png" alt="未确认" style={{ width: 50, height: 50, borderRadius: 4, objectFit: 'cover', opacity: 0.4 }} />
      ),
    },
    { title: '回监时间', dataIndex: 'returnTime', key: 'returnTime', width: 160 },
    {
      title: '监控录像',
      dataIndex: 'videoRecord',
      key: 'videoRecord',
      width: 120,
      render: (val) => val ? (
        <video
          src="https://www.w3schools.com/html/mov_bbb.mp4"
          controls
          style={{ width: 100, height: 50, objectFit: 'cover', borderRadius: 4 }}
        />
      ) : (
        <Tag color="default" icon={<VideoCameraOutlined />}>无录像</Tag>
      ),
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
      <div style={{ marginBottom: 12, flexShrink: 0 }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/prisoners')}
        >
          返回列表
        </Button>
      </div>

      <Row gutter={[16, 16]} style={{ flex: 1, overflow: 'hidden', display: 'flex' }}>
        <Col xs={24} sm={24} md={24} lg={10} xl={8} style={{ height: '100%' }}>
          <Card
            loading={loading}
            className="profile-card"
            style={{ borderRadius: 12, height: '100%', overflow: 'hidden' }}
            bodyStyle={{ padding: 0, height: '100%', overflow: 'auto' }}
          >
            <div className="profile-banner">
              <div className="banner-bg"></div>
              <div className="profile-content">
                <div className="profile-photo-large">
                  {detail?.photo ? (
                    <img src={detail.photo} alt={detail?.name} />
                  ) : (
                    <div className="photo-placeholder-large">
                      <UserOutlined style={{ fontSize: 50, color: '#fff' }} />
                    </div>
                  )}
                </div>
                <h2 className="profile-title">{detail?.name || '未知姓名'}</h2>
                <div className="profile-tags">
                  <Tag color={detail?.gender === '男' ? 'blue' : 'pink'} className="gender-tag">
                    {detail?.gender === '男' ? <ManOutlined /> : <WomanOutlined />}
                    {' '}{detail?.gender || '未知'}
                  </Tag>
                  <Tag color="gold" className="no-tag">{detail?.prisonerNo || '暂无编号'}</Tag>
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
                    <span className="stat-num">{detail?.sentence || '-'}</span>
                    <span className="stat-desc">刑期</span>
                  </div>
                </div>
                <div className="stat-box">
                  <div className="stat-icon ethnic-icon"><FileTextOutlined /></div>
                  <div className="stat-info">
                    <span className="stat-num">{detail?.ethnicity || '-'}</span>
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
                    <span className="cell-label">入狱原因</span>
                    <span className="cell-value">{detail?.incarcerationReason || '-'}</span>
                  </div>
                  <div className="info-cell">
                    <span className="cell-label">入狱日期</span>
                    <span className="cell-value">{detail?.incarcerationDate || '-'}</span>
                  </div>
                  <div className="info-cell">
                    <span className="cell-label">出狱日期</span>
                    <span className="cell-value highlight">{detail?.releaseDate || '-'}</span>
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
                    <span className="info-value mono">{detail?.idCard || '-'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">婚姻状况</span>
                    <span className="info-value">{detail?.maritalStatus || '-'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">籍贯</span>
                    <span className="info-value">{detail?.birthplace || '-'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">户籍地址</span>
                    <span className="info-value">{detail?.registeredAddress || '-'}</span>
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
          overflow: hidden;
        }

        .banner-bg {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 100px;
          background: linear-gradient(135deg, #1890ff 0%, #722ed1 50%, #eb2f96 100%);
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
          overflow: hidden;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
          border: 4px solid #fff;
        }

        .profile-photo-large img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .photo-placeholder-large {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
          background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
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
          border-bottom: 2px solid #1890ff;
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
          color: #1890ff;
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
