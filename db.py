import mysql.connector
from dotenv import load_dotenv
import os

# 加载 .env 文件
load_dotenv()

# 从环境变量中获取数据库配置
DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'port': os.getenv('DB_PORT', 3307)  # 默认使用端口3307
}

# 创建数据库连接
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"数据库连接失败: {err}")
        return None
