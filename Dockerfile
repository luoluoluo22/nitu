# 使用官方的 Python 镜像
FROM python:3.9-slim

# 安装 Nginx
RUN apt-get update && \
    apt-get install -y nginx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 80

# 设置环境变量
ENV FLASK_ENV=production

# 使用 CMD 来启动 Nginx 和 Flask 应用
CMD ["sh", "-c", "nginx -g 'daemon off;' & ./start.sh"]
