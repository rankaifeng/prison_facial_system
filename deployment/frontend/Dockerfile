FROM docker.1ms.run/library/nginx:alpine

# 删除默认配置
RUN rm /etc/nginx/conf.d/default.conf

# 复制构建产物和配置
COPY deployment/frontend/dist/ /usr/share/nginx/html/
COPY deployment/frontend/nginx.conf /etc/nginx/conf.d/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]