import { Form } from 'antd';
import { useAntdTable } from 'ahooks';
import http from '../server/axios';

const useQueryTable = (options) => {
    const {
        url,
        defaultParams = {},
        transformParams,
        defaultPageSize = 10,
        rowKey = 'id',
        manual = false,
    } = options || {};

    const [form] = Form.useForm();

    const getTableData = async ({ current, pageSize }, formData) => {
        const base = { page: current, limit: pageSize, ...defaultParams, ...(formData || {}) };
        const params = transformParams ? transformParams(base) : base;
        const res = await http.get(url, params);
        return { list: res?.data, total: res?.num };
    };

    const antdTable = useAntdTable(getTableData, {
        form,
        defaultParams: [{ current: 1, pageSize: defaultPageSize }, {}],
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
