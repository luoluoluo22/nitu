#!/bin/sh

# 启动 Gunicorn 服务器
exec gunicorn --bind 0.0.0.0:5000 app:app
