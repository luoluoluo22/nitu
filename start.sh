#!/bin/bash

# 启动 Flask 应用
echo "Starting Flask app..."
gunicorn -b 0.0.0.0:5000 app:app &

# 启动管理员 Flask 应用
echo "Starting admin Flask app..."
gunicorn -b 0.0.0.0:5002 admin:app

# 注意：这里我们假设 gunicorn 是安装在 requirements.txt 中的依赖
