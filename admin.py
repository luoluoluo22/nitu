from flask import Flask, render_template, request, redirect, url_for, make_response
from datetime import datetime, timedelta
import random
import string
import os
from dotenv import load_dotenv
import mysql.connector

# 加载 .env 文件
load_dotenv()

app = Flask(__name__)
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
COOKIE_DURATION_DAYS = 365

# 获取数据库连接
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        port=os.getenv('DB_PORT')
    )

# 读取所有授权码
def read_auth_codes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT auth_code, created_at, expires_at FROM auth_codes")
    auth_codes = cursor.fetchall()
    cursor.close()
    conn.close()
    return auth_codes

# 生成8位随机密钥
def generate_auth_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            resp = make_response(redirect(url_for('admin_index')))
            resp.set_cookie('admin_logged_in', 'true', max_age=COOKIE_DURATION_DAYS * 24 * 60 * 60)
            return resp
        else:
            return render_template('admin_login.html', error=True)
    return render_template('admin_login.html', error=False)

@app.route('/admin/logout')
def admin_logout():
    resp = make_response(redirect(url_for('admin_login')))
    resp.set_cookie('admin_logged_in', '', expires=0)
    return resp

@app.route('/admin')
def admin_index():
    if request.cookies.get('admin_logged_in') != 'true':
        return redirect(url_for('admin_login'))
    
    auth_codes = read_auth_codes()
    return render_template('admin_index.html', auth_codes=auth_codes)

@app.route('/admin/add', methods=['GET', 'POST'])
def admin_add():
    if request.cookies.get('admin_logged_in') != 'true':
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        
        new_code = generate_auth_code()
        created_at = datetime.now()
        expires_at_str = request.form.get('expires_at')
        expires_at = datetime.fromisoformat(expires_at_str) if expires_at_str else created_at + timedelta(days=30)
        
        cursor.execute(
            "INSERT INTO auth_codes (auth_code, created_at, expires_at) VALUES (%s, %s, %s)",
            (new_code, created_at, expires_at)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return redirect(url_for('admin_index'))
    
    return render_template('admin_add.html')

@app.route('/admin/delete/<auth_code>')
def admin_delete(auth_code):
    if request.cookies.get('admin_logged_in') != 'true':
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM auth_codes WHERE auth_code = %s", (auth_code,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_index'))

@app.route('/admin/edit/<auth_code>', methods=['GET', 'POST'])
def admin_edit(auth_code):
    if request.cookies.get('admin_logged_in') != 'true':
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT auth_code, created_at, expires_at FROM auth_codes WHERE auth_code = %s", (auth_code,))
    code_to_edit = cursor.fetchone()
    cursor.close()
    conn.close()

    if not code_to_edit:
        return redirect(url_for('admin_index'))

    if request.method == 'POST':
        expires_at = datetime.fromisoformat(request.form['expires_at'])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE auth_codes SET expires_at = %s WHERE auth_code = %s",
            (expires_at, auth_code)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin_index'))

    return render_template('admin_edit.html', auth_code=code_to_edit)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
