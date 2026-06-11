import React, { useMemo, useState } from 'react';
import { Button, message, Modal, Descriptions, Tag } from 'antd';
import { EyeOutlined, ExportOutlined } from '@ant-design/icons';
import SearchHeader from '@/components/search-header';
import TableLayout from '@/components/table-layout';
import useQueryTable from '@/hooks/useQueryTable';
import exportToCSV from '@/utils/export';
import { archive } from '@/api/globApi';

const PrisonerList = () => {
  const [detailVisible, setDetailVisible] = useState(false);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const { tableProps, loading, form, search } = useQueryTable({
    url: '/user_manage/archive/list',
    rowKey: 'bh',
  });

  const handleExport = () => {
    const data = tableProps.dataSource || [];
    if (data.length === 0) {
      message.warning('没有可导出的数据');
      return;
    }
    exportToCSV(data, columns.filter(col => col.key !== 'action'), '罪犯档案');
  };

  const handleViewDetail = async (record) => {
    setDetailLoading(true);
    setDetailVisible(true);
    try {
      const res = await archive.detail({ prisoner_no: record.bh });
      if (res?.code === 1 && res?.data) {
        setDetailData(res.data);
      } else {
        message.error(res?.msg || '获取详情失败');
        setDetailVisible(false);
      }
    } catch {
      message.error('获取详情失败');
      setDetailVisible(false);
    } finally {
      setDetailLoading(false);
    }
  };

  // 列表字段对应公安接口 XML 字段名
  const columns = [
    { title: '罪犯编号', dataIndex: 'bh', key: 'bh', width: 120 },
    { title: '姓名', dataIndex: 'xm', key: 'xm', width: 100 },
    { title: '性别', dataIndex: 'xb', key: 'xb', width: 60 },
    { title: '年龄', dataIndex: 'age', key: 'age', width: 60 },
    { title: '民族', dataIndex: 'mz', key: 'mz', width: 80 },
    { title: '罪名', dataIndex: 'zm', key: 'zm', width: 120, ellipsis: true },
    { title: '原判刑期', dataIndex: 'ypxq', key: 'ypxq', width: 120, ellipsis: true },
    { title: '监区', dataIndex: 'db', key: 'db', width: 80 },
    { title: '监室号', dataIndex: 'jsh', key: 'jsh', width: 80 },
    { title: '入监日期', dataIndex: 'rjrq', key: 'rjrq', width: 120 },
    { title: '在押状态', dataIndex: 'zyxz', key: 'zyxz', width: 80 },
    {
      title: '操作',
      key: 'action',
      width: 80,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetail(record)}
        >
          详情
        </Button>
      ),
    },
  ];

  // 搜索参数名对应数据库列名（后端负责筛选）
  const searchItems = useMemo(() => [
    {
      label: '罪犯编号',
      name: 'prisoner_no',
      type: 'input',
      props: { placeholder: '请输入罪犯编号' }
    },
    {
      label: '姓名',
      name: 'prisoner_name',
      type: 'input',
      props: { placeholder: '请输入姓名' }
    },
    {
      label: '监区',
      name: 'prison_area',
      type: 'input',
      props: { placeholder: '请输入监区' }
    },
    {
      label: '罪名',
      name: 'crime',
      type: 'input',
      props: { placeholder: '请输入罪名' }
    },
  ], []);

  // 详情弹窗 - 字段全部用 XML 原始名
  const renderDetailContent = () => {
    if (!detailData) return null;
    const d = detailData;
    const mediaList = d.mtxx || [];

    return (
      <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
        <Descriptions title="基本信息" bordered column={2} size="small">
          <Descriptions.Item label="罪犯编号">{d.bh}</Descriptions.Item>
          <Descriptions.Item label="姓名">{d.xm}</Descriptions.Item>
          <Descriptions.Item label="性别">{d.xb}</Descriptions.Item>
          <Descriptions.Item label="年龄">{d.age}</Descriptions.Item>
          <Descriptions.Item label="出生日期">{d.csrq}</Descriptions.Item>
          <Descriptions.Item label="身份证号">{d.sfzh}</Descriptions.Item>
          <Descriptions.Item label="民族">{d.mz}</Descriptions.Item>
          <Descriptions.Item label="文化程度">{d.bqwhcd}</Descriptions.Item>
          <Descriptions.Item label="婚姻状况">{d.hy}</Descriptions.Item>
          <Descriptions.Item label="籍贯">{d.jg}</Descriptions.Item>
          <Descriptions.Item label="家庭地址" span={2}>{d.jtmx}</Descriptions.Item>
          <Descriptions.Item label="罪名"><Tag color="red">{d.zm}</Tag></Descriptions.Item>
          <Descriptions.Item label="原判刑期">{d.ypxq}</Descriptions.Item>
          <Descriptions.Item label="刑期起日">{d.zr}</Descriptions.Item>
          <Descriptions.Item label="刑期止日">{d.syxq}</Descriptions.Item>
          <Descriptions.Item label="监区">{d.db}</Descriptions.Item>
          <Descriptions.Item label="监室号/床号">{d.jsh} / {d.cwh}</Descriptions.Item>
          <Descriptions.Item label="在押状态"><Tag color="green">{d.zyxz}</Tag></Descriptions.Item>
          <Descriptions.Item label="入监日期">{d.rjrq}</Descriptions.Item>
          <Descriptions.Item label="逮捕机关">{d.dbjg}</Descriptions.Item>
          <Descriptions.Item label="判决机关">{d.pjjg}</Descriptions.Item>
          <Descriptions.Item label="判决书号" span={2}>{d.pjzh}</Descriptions.Item>
        </Descriptions>

        {d.fzss && (
          <>
            <div style={{ marginTop: 16, marginBottom: 8, fontWeight: 600, fontSize: 14 }}>犯罪事实</div>
            <div style={{ background: '#fafafa', padding: 12, borderRadius: 8, fontSize: 13, lineHeight: 1.8 }}>
              {d.fzss}
            </div>
          </>
        )}

        {mediaList.length > 0 && (
          <>
            <div style={{ marginTop: 16, marginBottom: 8, fontWeight: 600, fontSize: 14 }}>
              媒体信息 ({mediaList.length}条)
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
              {mediaList.map((m, idx) => (
                <div key={idx} style={{
                  background: '#fafafa', padding: 12, borderRadius: 8,
                  border: '1px solid #f0f0f0', minWidth: 200
                }}>
                  <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>{m.mtbmm}</div>
                  <div style={{ fontSize: 13 }}>{m.xp}</div>
                  {m.bz && <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>备注: {m.bz}</div>}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    );
  };

  return (
    <div>
      <SearchHeader
        form={form}
        items={searchItems}
        onSearch={search.submit}
        onReset={search.reset}
      />
      <TableLayout
        headerLayout={
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 10, gap: 12 }}>
            <Button type="primary" icon={<ExportOutlined />} onClick={handleExport}>
              导出
            </Button>
          </div>
        }
        tableProps={tableProps}
        loading={loading}
        columns={columns}
      />

      <Modal
        title="罪犯档案详情"
        open={detailVisible}
        onCancel={() => { setDetailVisible(false); setDetailData(null); }}
        footer={null}
        width={800}
        destroyOnClose
      >
        {detailLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>加载中...</div>
        ) : (
          renderDetailContent()
        )}
      </Modal>
    </div>
  );
};

export default PrisonerList;
