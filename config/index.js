const MODE = import.meta.env.MODE;
const apiBaseUrl = 'http://127.0.0.1:8000/'

const returnBaseUrl = () => {
    if (MODE === 'development') {
        return apiBaseUrl;
    }
    const parsedUrl = window.location.href.match(/(http[s]?:\/\/[^\/]+)/);
    if (parsedUrl && parsedUrl[0]) {
        const base = `${parsedUrl[0].replace(/:\d+$/, '')}:8793/api/`;
        return base;
    }
}
export const BASE_URL = returnBaseUrl();
