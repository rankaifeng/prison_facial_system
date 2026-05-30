import axios from 'axios';
import { message } from 'antd';
import { BASE_URL } from '../../config/index.js';
import cache from '@/utils/cache';
import {
    mockPrisons,
    mockPrisoners,
    mockPrisoner,
    mockExitRecords,
    mockExitRecordsForPrisoner,
    mockRealtimeStatistics,
    mockWorkStatistics,
    mockExitStatistics,
    mockMessages,
    mockAccounts,
    mockPrisonerArchive,
    mockResponse,
    mockListResponse
} from '@/api/mockData';

// Mock API handler
const mockHandler = (url, params = {}) => {
    // Add delay to simulate network
    const delay = 300;

    // Prison List
    if (url.includes('prison_info_list')) {
        return new Promise(resolve => {
            setTimeout(() => resolve(mockResponse(mockPrisons())), delay);
        });
    }

    // Prisoner List
    if (url.includes('prisoner_info_list')) {
        const { page = 1, limit = 10 } = params;
        return new Promise(resolve => {
            setTimeout(() => resolve(mockListResponse(mockPrisoners(100), page, limit)), delay);
        });
    }

    // Prisoner Detail
    if (url.includes('prisoner_info_detail')) {
        const id = params.id;
        const index = parseInt(id?.replace(/[^0-9]/g, '') || '0', 10) || 0;
        return new Promise(resolve => {
            setTimeout(() => resolve(mockResponse(mockPrisoner(index % 100))), delay);
        });
    }

    // Exit Records
    if (url.includes('exit_record_list')) {
        const { page = 1, limit = 10, prisonerId } = params;
        if (prisonerId) {
            const records = mockExitRecordsForPrisoner(prisonerId, 20);
            return new Promise(resolve => {
                setTimeout(() => resolve(mockResponse(records)), delay);
            });
        }
        const allRecords = mockExitRecords(30);
        return new Promise(resolve => {
            setTimeout(() => resolve(mockListResponse(allRecords, page, limit)), delay);
        });
    }

    // Exit Statistics
    if (url.includes('exit_statistics_list')) {
        const { page = 1, limit = 10, prisonName } = params;
        let allData = mockExitStatistics(50);
        if (prisonName) {
            allData = allData.filter(item => item.prisonName === prisonName);
        }
        return new Promise(resolve => {
            setTimeout(() => resolve(mockListResponse(allData, page, limit)), delay);
        });
    }

    // Realtime Statistics
    if (url.includes('realtime_statistics')) {
        return new Promise(resolve => {
            setTimeout(() => resolve(mockResponse(mockRealtimeStatistics())), delay);
        });
    }

    // Work Statistics
    if (url.includes('work_statistics_list')) {
        return new Promise(resolve => {
            setTimeout(() => resolve(mockResponse(mockWorkStatistics())), delay);
        });
    }

    // Messages
    if (url.includes('message_list')) {
        const { limit = 10 } = params;
        return new Promise(resolve => {
            setTimeout(() => resolve(mockResponse(mockMessages(limit))), delay);
        });
    }

    // Account List
    if (url.includes('account_list')) {
        const { page = 1, limit = 10 } = params;
        return new Promise(resolve => {
            setTimeout(() => resolve(mockListResponse(mockAccounts(20), page, limit)), delay);
        });
    }

    // Prisoner Archive
    if (url.includes('prisoner_archive_list')) {
        const { page = 1, limit = 10 } = params;
        return new Promise(resolve => {
            setTimeout(() => resolve(mockListResponse(mockPrisonerArchive(50), page, limit)), delay);
        });
    }

    // Default: return empty success
    return new Promise(resolve => {
        setTimeout(() => resolve(mockResponse(null)), delay);
    });
};

// Check if should use mock (disabled - using real backend)
const USE_MOCK = false;

const service = axios.create({
    baseURL: BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json; charset=utf-8',
    },
});

service.interceptors.request.use(
    (config) => {
        const token = cache.getVal("token");
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        console.error('Request Error:', error);
        return Promise.reject(error);
    }
);

service.interceptors.response.use(
    (response) => {
        const res = response.data;
        if (res.msg && res.msg.includes("无效")) {
            cache.clearVal();
            window.location.href = '/login';
            return;
        }
        return res;
    },
    (error) => {
        let msg = '网络连接异常';
        console.log("error", error);

        if (error.response) {
            const { status } = error.response;
            switch (status) {
                case 401:
                    msg = '登录已过期，请重新登录';
                    cache.clearVal();
                    message.error(msg);
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 1500);
                    break;
                case 403:
                    msg = '您没有权限访问该资源';
                    break;
                case 404:
                    msg = '请求的资源不存在';
                    break;
                case 500:
                    msg = '服务器内部错误，请联系管理员';
                    break;
                default:
                    msg = error.response.data?.msg || '未知错误';
            }
        }
        message.error(msg);
        return Promise.reject(error);
    }
);

const http = {
    get(url, params, timeout) {
        if (USE_MOCK) {
            return mockHandler(url, params);
        }
        const config = { params };
        if (timeout) {
            config.timeout = timeout;
        }
        return service.get(url, config);
    },
    post(url, data) {
        if (USE_MOCK) {
            return mockHandler(url, data);
        }
        if (data instanceof FormData) {
            return service.post(url, data);
        }
        const formData = new FormData();
        for (const key in data) {
            const value = data[key];
            if (value instanceof Blob || typeof value === 'string' || typeof value === 'number') {
                formData.append(key, value);
            } else if (Array.isArray(value)) {
                value.forEach(item => {
                    if (item instanceof Blob) {
                        formData.append('file_list', item);
                    } else {
                        formData.append(key, item);
                    }
                });
            } else if (value !== undefined && value !== null) {
                formData.append(key, value);
            }
        }
        return service.post(url, formData);
    },
    put(url, data) {
        if (USE_MOCK) {
            return mockHandler(url, data);
        }
        return service.put(url, data);
    },
    delete(url, params) {
        if (USE_MOCK) {
            return mockHandler(url, params);
        }
        return service.delete(url, { params });
    }
};

export default http;
