const MODE = import.meta.env.MODE;
const apiBaseUrl = 'http://127.0.0.1:8000/'

const returnBaseUrl = () => {
    if (MODE === 'development') {
        return '/api/';
    }
    // 生产环境：通过 Nginx 代理，使用同源地址
    const parsedUrl = window.location.href.match(/(http[s]?:\/\/[^\/]+)/);
    if (parsedUrl && parsedUrl[0]) {
        return `${parsedUrl[0]}/api/`;
    }
}
export const BASE_URL = returnBaseUrl();
