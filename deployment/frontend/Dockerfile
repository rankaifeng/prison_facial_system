FROM docker.io/library/nginx:1.27-alpine

# 删除默认配置
RUN rm /etc/nginx/conf.d/default.conf

# 复制 Nginx 配置
COPY deployment/frontend/nginx.conf /etc/nginx/conf.d/

# 复制前端构建产物
COPY dist/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
