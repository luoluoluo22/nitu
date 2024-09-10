# 使用官方的 Python 3.9 镜像作为基础镜像
FROM python:3.9

# 设置工作目录
WORKDIR /app

# 复制项目的依赖文件到容器中
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码到容器中
COPY . .

# 暴露应用使用的端口
EXPOSE 5000
EXPOSE 5002

# 运行 start.sh 脚本来启动应用
CMD ["./start.sh"]
