from flask import Flask
import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 设置数据库连接池配置
DB_POOL_NAME = "mypool"
DB_POOL_SIZE = 5  # 连接池大小

db_config = {
    "host": os.getenv('DB_HOST'),
    "user": os.getenv('DB_USER'),
    "password": os.getenv('DB_PASSWORD'),
    "database": os.getenv('DB_NAME'),
    "port": 3307,
    "pool_name": DB_POOL_NAME,
    "pool_size": DB_POOL_SIZE
}

# 初始化连接池
db_pool = mysql.connector.pooling.MySQLConnectionPool(pool_reset_session=True, **db_config)

# 获取数据库连接（从连接池）
def get_db_connection():
    return db_pool.get_connection()
