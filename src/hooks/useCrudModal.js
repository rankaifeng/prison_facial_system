import { useState } from 'react';
import { message } from 'antd';
import { useRequest } from 'ahooks';
import http from '@/server/axios';

const useCrudModal = (baseApiUrl, refresh) => {
    const [modalOpen, setModalOpen] = useState(false);
    const [editingRecord, setEditingRecord] = useState(null);

    const { run: submit, loading } = useRequest(
        (values) => {
            const isEdit = !!editingRecord;
            const apiUrl = isEdit ? `${baseApiUrl}_update` : `${baseApiUrl}_add`;
            const payload = isEdit ? { ...editingRecord, ...values } : values;
            return http.post(apiUrl, payload);
        },
        {
            manual: true,
            onSuccess: () => {
                const action = editingRecord ? '更新' : '新增';
                message.success(`${action}成功`);
                setModalOpen(false);
                refresh();
            },
        }
    );

    const openForAdd = () => {
        setEditingRecord(null);
        setModalOpen(true);
    };

    const openForEdit = (record) => {
        setEditingRecord(record);
        setModalOpen(true);
    };

    const modalProps = {
        open: modalOpen,
        initialData: editingRecord,
        onCancel: () => setModalOpen(false),
        onOk: submit,
        confirmLoading: loading,
    };

    const modalActions = {
        openForAdd,
        openForEdit,
    };

    return { modalProps, modalActions };
};

export default useCrudModal;
