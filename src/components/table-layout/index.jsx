import React, { useMemo } from 'react';
import './index.less';
import { Table } from 'antd';

const TableLayout = (props) => {
    const { tableProps, loading, columns, headerLayout, hideIndex = false } = props;

    const { pagination, dataSource, ...restTableProps } = tableProps;

    const showTotal = (total, range) => {
        return `第${pagination.current}页-${pagination.pageSize}条 / 共${total}条`;
    };

    const customizedPagination = pagination ? {
        ...pagination,
        showTotal: showTotal,
    } : false;

    const isTreeData = useMemo(() => {
        if (!dataSource || !Array.isArray(dataSource)) return false;
        return dataSource.some(item => item && item.children && item.children.length > 0);
    }, [dataSource]);

    const columnsWithIndex = useMemo(() => {
        // 树形数据或设置了 hideIndex 不显示序号列
        if (isTreeData || hideIndex) {
            return columns || [];
        }

        const indexColumn = {
            title: '序号',
            dataIndex: '_index',
            key: '_index',
            width: 70,
            align: 'center',
            render: (_, record, index) => {
                if (record.parent_id != null) {
                    return '';
                }
                const current = pagination?.current || 1;
                const pageSize = pagination?.pageSize || 10;
                const num = (current - 1) * pageSize + index + 1;
                const rank = num <= 5 ? num : 0;
                return (
                    <span className={`index-cell ${rank > 0 ? `index-${rank}` : ''}`}>
                        {num}
                    </span>
                );
            },
        };

        const processedColumns = [...(columns || [])];

        // processedColumns.forEach(col => {
        //     if (col.key === 'action' || col.title === '操作') {
        //         col.fixed = 'right';
        //     }
        // });

        return [indexColumn, ...processedColumns];
    }, [columns, pagination, isTreeData, hideIndex]);

    return (
        <div className='table-layout'>
            {headerLayout && <div className="table-header">{headerLayout}</div>}
            <Table
                bordered
                {...restTableProps}
                dataSource={dataSource}
                loading={loading}
                columns={columnsWithIndex}
                scroll={{ x: 'max-content', y: 'calc(100vh - 340px)' }}
                pagination={customizedPagination}
            />
        </div>
    );
};

export default TableLayout;
