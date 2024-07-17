from flask import Flask, jsonify, request, render_template, redirect, url_for, make_response
from datetime import datetime, timedelta, timezone
import random
import string
import re
import imaplib
import email
from bs4 import BeautifulSoup
import os
import csv
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

app = Flask(__name__)

# 存储最近一封邮件内容及其接收时间
latest_email = {"code": "无", "received_at": datetime.now(), "sent_at": "未知"}

# 从环境变量中读取配置信息
IMAP_SERVER = os.getenv('IMAP_SERVER')
IMAP_PORT = int(os.getenv('IMAP_PORT'))
USERNAME = os.getenv('USERNAME')
AUTHORIZATION_CODE = os.getenv('AUTHORIZATION_CODE')
AUTH_CODE_FILE = os.getenv('AUTH_CODE_FILE')
AUTH_CODE_EXPIRY_DAYS = int(os.getenv('AUTH_CODE_EXPIRY_DAYS'))
COOKIE_DURATION_DAYS = int(os.getenv('COOKIE_DURATION_DAYS'))

# 初始化CSV文件
def init_csv():
    if not os.path.exists(AUTH_CODE_FILE):
        with open(AUTH_CODE_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['auth_code', 'created_at', 'expires_at'])

# 读取所有有效的授权码
def get_valid_auth_codes():
    valid_auth_codes = []
    auth_code_data = {}
    if os.path.exists(AUTH_CODE_FILE):
        with open(AUTH_CODE_FILE, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # 跳过标题行
            for row in reader:
                auth_code, created_at, expires_at = row
                expires_at = datetime.fromisoformat(expires_at)
                created_at = datetime.fromisoformat(created_at)
                if expires_at > datetime.now():
                    valid_auth_codes.append(auth_code)
                    auth_code_data[auth_code] = {
                        "created_at": created_at,
                        "expires_at": expires_at
                    }
    if not valid_auth_codes:
        raise Exception("未找到有效的授权码")
    return valid_auth_codes, auth_code_data

# 初始化CSV文件
init_csv()

def get_email_body(msg):
    email_body = None
    for part in msg.walk():
        content_type = part.get_content_type()
        if content_type == 'text/plain':
            email_body = part.get_payload(decode=True).decode('utf-8')
            break
        elif content_type == 'text/html':
            html_content = part.get_payload(decode=True).decode('utf-8')
            soup = BeautifulSoup(html_content, 'html.parser')
            email_body = soup.get_text()
            break
    return email_body

def check_emails():
    print("Checking emails...")  # 确保函数被调用
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(USERNAME, AUTHORIZATION_CODE)
        mail.select('inbox')
        status, email_ids = mail.search(None, 'ALL')
        if status == 'OK':
            email_id_list = email_ids[0].split()
            if not email_id_list:
                print("没有找到新的邮件。")
                mail.close()
                return

            latest_email_id = email_id_list[-1]
            status, data = mail.fetch(latest_email_id, '(RFC822)')
            if status == 'OK' and data:
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                email_body = get_email_body(msg)
                print(email_body)
                if email_body:
                    email_date = msg['Date']
                    email_sent_time = email.utils.parsedate_to_datetime(email_date).astimezone(timezone.utc)
                    email_sent_time_str = email_sent_time.strftime('%Y-%m-%d %H:%M:%S')
                    current_time = datetime.now(timezone.utc)
                    if current_time - email_sent_time > timedelta(minutes=15):
                        email_body = "无"
                    latest_email["received_at"] = datetime.now()
                    latest_email["sent_at"] = email_sent_time_str
                    match = re.search(r'\D(\d{6})\D', email_body)
                    if match:
                        latest_email["code"] = match.group(1)
                    else:
                        latest_email["code"] = "无"
                else:
                    print("邮件正文为空，跳过。")
            else:
                print("无法获取邮件内容，跳过。")
        mail.store(latest_email_id, '+FLAGS', '\\Seen')
        mail.close()
    except Exception as e:
        print(f"发生错误：{e}")

@app.route('/')
def index():
    auth_code = request.cookies.get('auth_code')
    valid_auth_codes, auth_code_data = get_valid_auth_codes()  # 每次加载页面时重新读取CSV文件
    if auth_code in valid_auth_codes:
        auth_code_info = auth_code_data[auth_code]
        created_at = auth_code_info['created_at']
        expires_at = auth_code_info['expires_at']
        remaining_days = (expires_at - datetime.now()).days
        return render_template('index.html', 
                               code=latest_email['code'], 
                               received_at=latest_email['received_at'].strftime('%H:%M:%S'), 
                               remaining_days=remaining_days,
                               created_at=created_at.strftime('%Y-%m-%d %H:%M:%S'),
                               expires_at=expires_at.strftime('%Y-%m-%d %H:%M:%S'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = False
    if request.method == 'POST':
        auth_code = request.form['auth_code']
        valid_auth_codes, auth_code_data = get_valid_auth_codes()  # 每次登录时重新读取CSV文件
        if auth_code in valid_auth_codes:
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('auth_code', auth_code, max_age=COOKIE_DURATION_DAYS * 24 * 60 * 60)
            return resp
        error = True
    return render_template('login.html', error=error)

@app.route('/update_email', methods=['GET'])
def update_email():
    auth_code = request.cookies.get('auth_code')
    valid_auth_codes, auth_code_data = get_valid_auth_codes()  # 每次更新邮件时重新读取CSV文件
    if auth_code in valid_auth_codes:
        check_emails()
        auth_code_info = auth_code_data[auth_code]
        expires_at = auth_code_info['expires_at']
        remaining_days = (expires_at - datetime.now()).days
        return jsonify({"status": "success", "code": latest_email["code"]}), 200
    return jsonify({"status": "error", "message": "Unauthorized"}), 401

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
