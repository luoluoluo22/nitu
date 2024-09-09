from flask import Flask, render_template, request, redirect, url_for, make_response
from datetime import datetime, timedelta
import random
import string
import csv
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

app = Flask(__name__)
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
AUTH_CODE_FILE = os.getenv('AUTH_CODE_FILE')
COOKIE_DURATION_DAYS = int(os.getenv('COOKIE_DURATION_DAYS'))

# 初始化CSV文件
def init_csv():
    if not os.path.exists(AUTH_CODE_FILE):
        with open(AUTH_CODE_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['auth_code', 'created_at', 'expires_at'])

# 读取所有授权码
def read_auth_codes():
    auth_codes = []
    if os.path.exists(AUTH_CODE_FILE):
        with open(AUTH_CODE_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                row['created_at'] = datetime.fromisoformat(row['created_at'])
                row['expires_at'] = datetime.fromisoformat(row['expires_at'])
                auth_codes.append(row)
    return auth_codes

# 写入所有授权码
def write_auth_codes(auth_codes):
    with open(AUTH_CODE_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['auth_code', 'created_at', 'expires_at'])
        writer.writeheader()
        for code in auth_codes:
            writer.writerow({
                'auth_code': code['auth_code'],
                'created_at': code['created_at'].isoformat(timespec='seconds'),
                'expires_at': code['expires_at'].isoformat(timespec='seconds')
            })

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

@app.route('/')
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
        auth_codes = read_auth_codes()
        new_code = generate_auth_code()
        while any(code['auth_code'] == new_code for code in auth_codes):
            new_code = generate_auth_code()
        
        created_at = datetime.now()
        expires_at_str = request.form.get('expires_at')
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
        else:
            expires_at = created_at + timedelta(days=30)
        
        auth_codes.append({
            'auth_code': new_code,
            'created_at': created_at,
            'expires_at': expires_at
        })
        write_auth_codes(auth_codes)
        return redirect(url_for('admin_index'))
    
    return render_template('admin_add.html')

@app.route('/admin/delete/<auth_code>')
def admin_delete(auth_code):
    if request.cookies.get('admin_logged_in') != 'true':
        return redirect(url_for('admin_login'))

    auth_codes = read_auth_codes()
    auth_codes = [code for code in auth_codes if code['auth_code'] != auth_code]
    write_auth_codes(auth_codes)
    return redirect(url_for('admin_index'))

@app.route('/admin/edit/<auth_code>', methods=['GET', 'POST'])
def admin_edit(auth_code):
    if request.cookies.get('admin_logged_in') != 'true':
        return redirect(url_for('admin_login'))

    auth_codes = read_auth_codes()
    code_to_edit = next((code for code in auth_codes if code['auth_code'] == auth_code), None)
    if not code_to_edit:
        return redirect(url_for('admin_index'))

    if request.method == 'POST':
        expires_at = datetime.fromisoformat(request.form['expires_at'])
        code_to_edit['expires_at'] = expires_at
        write_auth_codes(auth_codes)
        return redirect(url_for('admin_index'))

    return render_template('admin_edit.html', auth_code=code_to_edit)

if __name__ == '__main__':
    init_csv()
    app.run(host='0.0.0.0', port=5002)
