import { Form } from 'antd';
import { useAntdTable } from 'ahooks';
import http from '../server/axios';

const useQueryTable = (options) => {
    const {
        url,
        defaultParams = {},
        transformParams,
        defaultPageSize = 10,
        defaultCurrentPage = 1,
        rowKey = 'id',
        manual = false,
    } = options || {};

    const [form] = Form.useForm();

    const getTableData = async ({ current, pageSize }, formData) => {
        // 处理 dateRange 类型字段，转换为时间戳
        const processedFormData = { ...formData };
        if (processedFormData && processedFormData.date_range) {
            const val = processedFormData.date_range;
            if (Array.isArray(val) && val.length === 2) {
                const [start, end] = val;
                const startTs = start?.valueOf ? start.valueOf() : new Date(start).getTime();
                const endTs = end?.valueOf ? end.valueOf() : new Date(end).getTime();
                processedFormData.start_timestamp = String(startTs);
                processedFormData.end_timestamp = String(endTs);
            }
            delete processedFormData.date_range;
        }
        // 移除空值
        Object.keys(processedFormData).forEach(key => {
            if (processedFormData[key] === undefined || processedFormData[key] === '' || processedFormData[key] === null) {
                delete processedFormData[key];
            }
        });
        const base = { page: current, limit: pageSize, ...defaultParams, ...processedFormData };
        const params = transformParams ? transformParams(base) : base;
        const res = await http.get(url, params);
        return { list: res?.data, total: res?.num };
    };

    const antdTable = useAntdTable(getTableData, {
        form,
        defaultParams: [{ current: defaultCurrentPage, pageSize: defaultPageSize }, defaultParams],
        manual,
    });

    const { tableProps, search, refresh, run, params, loading, pagination } = antdTable;

    return {
        form,
        loading,
        search,
        refresh,
        run,
        params,
        pagination,
        tableProps: {
            ...tableProps,
            rowKey,
        },
    };
};

export default useQueryTable;
