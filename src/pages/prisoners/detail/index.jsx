import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Row, Col, Tag, Timeline, Button, Empty } from 'antd';
import {
  ArrowLeftOutlined,
  UserOutlined,
  ManOutlined,
  WomanOutlined,
  CalendarOutlined,
  EnvironmentOutlined,
  FileTextOutlined,
  LockOutlined,
  HistoryOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import { prisoner, exitRecord } from '@/api/globApi';

const PrisonerDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState(null);
  const [exitRecords, setExitRecords] = useState([]);
  const [loading, setLoading] = useState(false);

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
      setExitRecords(exitData?.data || []);
    } catch (error) {
      console.error('获取详情失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getConfirmTag = (confirmed) => {
    if (confirmed) {
      return <Tag color="success" icon={<CheckCircleOutlined />}>已确认</Tag>;
    }
    return <Tag color="error" icon={<CloseCircleOutlined />}>未确认</Tag>;
  };

  return (
    <div style={{ padding: '0 0 20px 0', height: '100%', overflow: 'auto' }}>
      <div style={{ marginBottom: 16 }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/prisoners')}
        >
          返回列表
        </Button>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={24} md={24} lg={8} xl={7}>
          <Card
            loading={loading}
            className="profile-card"
            style={{ borderRadius: 12, overflow: 'hidden' }}
          >
            <div className="profile-header">
              <div className="profile-photo">
                {detail?.photo ? (
                  <img src={detail.photo} alt={detail?.name} />
                ) : (
                  <div className="photo-placeholder">
                    <UserOutlined style={{ fontSize: 60, color: '#ccc' }} />
                  </div>
                )}
              </div>
              <div className="profile-name">
                <h2>{detail?.name || '未知姓名'}</h2>
                <Tag color={detail?.gender === '男' ? 'blue' : 'pink'}>
                  {detail?.gender === '男' ? <ManOutlined /> : <WomanOutlined />}
                  {' '}{detail?.gender || '未知'}
                </Tag>
                <Tag color="purple">{detail?.prisonerNo || '暂无编号'}</Tag>
              </div>
            </div>
            <div className="profile-stats">
              <div className="stat-item">
                <span className="stat-label">年龄</span>
                <span className="stat-value">{detail?.age || '-'}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">刑期</span>
                <span className="stat-value">{detail?.sentence || '-'}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">民族</span>
                <span className="stat-value">{detail?.ethnicity || '-'}</span>
              </div>
            </div>
          </Card>

          <Card
            loading={loading}
            title={
              <span>
                <FileTextOutlined />基本信息
              </span>
            }
            style={{ borderRadius: 12, marginTop: 16 }}
          >
            <div className="info-list">
              <div className="info-item">
                <span className="info-label">身份证号</span>
                <span className="info-value">{detail?.idCard || '-'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">婚姻状况</span>
                <span className="info-value">{detail?.maritalStatus || '-'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">籍贯</span>
                <span className="info-value">{detail?.birthplace || '-'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">户籍地址</span>
                <span className="info-value">{detail?.registeredAddress || '-'}</span>
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={24} md={24} lg={16} xl={17}>
          <Card
            loading={loading}
            title={
              <span>
                <LockOutlined />服刑信息
              </span>
            }
            style={{ borderRadius: 12, marginBottom: 16 }}
          >
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={8}>
                <div className="info-card">
                  <div className="info-card-icon prison">
                    <LockOutlined />
                  </div>
                  <div className="info-card-content">
                    <span className="info-card-label">入狱原因</span>
                    <span className="info-card-value">{detail?.incarcerationReason || '-'}</span>
                  </div>
                </div>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <div className="info-card">
                  <div className="info-card-icon date">
                    <CalendarOutlined />
                  </div>
                  <div className="info-card-content">
                    <span className="info-card-label">入狱日期</span>
                    <span className="info-card-value">{detail?.incarcerationDate || '-'}</span>
                  </div>
                </div>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <div className="info-card">
                  <div className="info-card-icon release">
                    <CalendarOutlined />
                  </div>
                  <div className="info-card-content">
                    <span className="info-card-label">出狱日期</span>
                    <span className="info-card-value">{detail?.releaseDate || '-'}</span>
                  </div>
                </div>
              </Col>
            </Row>
          </Card>

          <Card
            loading={loading}
            title={
              <span>
                <HistoryOutlined />出监记录
              </span>
            }
            style={{ borderRadius: 12 }}
          >
            {exitRecords.length > 0 ? (
              <Timeline
                items={exitRecords.map((record, index) => ({
                  color: record.returnTime ? 'green' : 'gray',
                  key: record.id || index,
                  children: (
                    <div className="timeline-item">
                      <div className="timeline-header">
                        <Tag color="blue">{record.exitReason || '出监'}</Tag>
                        <span className="timeline-date">{record.exitTime || '-'}</span>
                      </div>
                      <div className="timeline-content">
                        <div className="timeline-row">
                          <EnvironmentOutlined />
                          <span>就医医院：{record.hospital || '-'}</span>
                        </div>
                        <div className="timeline-confirms">
                          <span className="confirm-item">民警 {getConfirmTag(record.policeConfirm)}</span>
                          <span className="confirm-item">特警 {getConfirmTag(record.swatConfirm)}</span>
                          <span className="confirm-item">武警 {getConfirmTag(record.armedPoliceConfirm)}</span>
                        </div>
                        {record.returnTime && (
                          <div className="timeline-row return">
                            <CalendarOutlined />
                            <span>回监时间：{record.returnTime}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ),
                }))}
              />
            ) : (
              <Empty description="暂无出监记录" />
            )}
          </Card>
        </Col>
      </Row>

      <style>{`
        .profile-card {
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }

        .profile-header {
          text-align: center;
          padding: 20px 0;
          border-bottom: 1px solid #f0f0f0;
        }

        .profile-photo {
          width: 140px;
          height: 180px;
          margin: 0 auto 16px;
          border-radius: 8px;
          overflow: hidden;
          background: #f5f5f5;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .profile-photo img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .photo-placeholder {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        .profile-name h2 {
          margin: 0 0 8px 0;
          font-size: 20px;
          font-weight: 600;
        }

        .profile-name .ant-tag {
          margin: 4px;
        }

        .profile-stats {
          display: flex;
          justify-content: space-around;
          padding: 16px 0;
        }

        .profile-stats .stat-item {
          text-align: center;
        }

        .profile-stats .stat-label {
          display: block;
          font-size: 12px;
          color: #999;
          margin-bottom: 4px;
        }

        .profile-stats .stat-value {
          font-size: 16px;
          font-weight: 600;
          color: #333;
        }

        .info-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .info-item {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px dashed #f0f0f0;
        }

        .info-item:last-child {
          border-bottom: none;
        }

        .info-label {
          color: #999;
          font-size: 13px;
        }

        .info-value {
          color: #333;
          font-size: 13px;
          font-weight: 500;
          text-align: right;
          max-width: 60%;
          word-break: break-all;
        }

        .info-card {
          display: flex;
          align-items: center;
          padding: 16px;
          background: #fafafa;
          border-radius: 8px;
          border: 1px solid #f0f0f0;
        }

        .info-card-icon {
          width: 48px;
          height: 48px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 20px;
          margin-right: 12px;
        }

        .info-card-icon.prison {
          background: rgba(24, 144, 255, 0.1);
          color: #1890ff;
        }

        .info-card-icon.date {
          background: rgba(82, 196, 26, 0.1);
          color: #52c41a;
        }

        .info-card-icon.release {
          background: rgba(255, 77, 79, 0.1);
          color: #ff4d4f;
        }

        .info-card-content {
          display: flex;
          flex-direction: column;
        }

        .info-card-label {
          font-size: 12px;
          color: #999;
          margin-bottom: 4px;
        }

        .info-card-value {
          font-size: 14px;
          font-weight: 600;
          color: #333;
        }

        .timeline-item {
          padding: 4px 0;
        }

        .timeline-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }

        .timeline-date {
          font-size: 12px;
          color: #999;
        }

        .timeline-content {
          background: #fafafa;
          padding: 12px;
          border-radius: 8px;
          font-size: 13px;
        }

        .timeline-row {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #666;
          margin-bottom: 8px;
        }

        .timeline-row:last-child {
          margin-bottom: 0;
        }

        .timeline-row.return {
          color: #52c41a;
          font-weight: 500;
        }

        .timeline-confirms {
          display: flex;
          gap: 16px;
          flex-wrap: wrap;
          margin-top: 8px;
        }

        .confirm-item {
          font-size: 12px;
        }

        .ant-card-head {
          min-height: 48px;
          padding: 0 16px;
        }

        .ant-card-head-title {
          font-size: 15px;
          font-weight: 600;
        }

        .ant-card-body {
          padding: 16px;
        }

        .ant-timeline {
          padding-top: 8px;
        }
      `}</style>
    </div>
  );
};

export default PrisonerDetail;
