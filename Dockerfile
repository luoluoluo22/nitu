# 使用官方 Python 镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 并安装依赖项
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# 复制项目文件
COPY . .

# 暴露应用程序端口
EXPOSE 5000 5002

# 设置环境变量（可选）
ENV FLASK_ENV=production

# 启动应用程序
CMD python app.py & python admin.py
