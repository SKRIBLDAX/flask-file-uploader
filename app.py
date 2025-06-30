import os
import json
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash, session
from functools import wraps

UPLOAD_FOLDER = 'uploads'
USERS_FILE = 'users.json'
FILES_FILE = 'files.json'
ADMIN_USERNAME = 'SKRIBLDAX'
ADMIN_PASSWORD = 'kakawka2281337'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'supersecretkey'

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f)

def load_files():
    if not os.path.exists(FILES_FILE):
        return {}
    with open(FILES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_files(files):
    with open(FILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(files, f)

def allowed_file(filename):
    return filename != ''

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('username'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def is_admin():
    return session.get('username') == ADMIN_USERNAME

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users()
        if username in users:
            flash('Пользователь уже существует!')
        elif not username or not password:
            flash('Заполните все поля!')
        else:
            users[username] = password
            save_users(users)
            flash('Регистрация успешна! Теперь войдите.')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['username'] = username
            flash('Вы вошли как администратор!')
            return redirect(url_for('upload_file'))
        elif username in users and users[username] == password:
            session['username'] = username
            flash('Вы успешно вошли!')
            return redirect(url_for('upload_file'))
        else:
            flash('Неверный логин или пароль!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Вы вышли из аккаунта.')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Нет файла в запросе')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Файл не выбран')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = file.filename
            if filename is None:
                flash('Некорректное имя файла')
                return redirect(request.url)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            files = load_files()
            files[filename] = session['username']
            save_files(files)
            flash('Файл успешно загружен')
            return redirect(url_for('uploaded_files'))
    return render_template('upload.html')

@app.route('/files')
@login_required
def uploaded_files():
    files = load_files()
    all_files = list(files.keys())
    is_admin_flag = is_admin()
    username = session.get('username')
    return render_template('files.html', files=all_files, is_admin=is_admin_flag, username=username, files_owners=files)

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    files = load_files()
    if is_admin() or files.get(filename) == session['username']:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    flash('Нет доступа к этому файлу!')
    return redirect(url_for('uploaded_files'))

@app.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_file(filename):
    files = load_files()
    if is_admin() or files.get(filename) == session['username']:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            files.pop(filename, None)
            save_files(files)
            flash(f'Файл {filename} удалён')
        else:
            flash('Файл не найден')
    else:
        flash('Нет доступа для удаления файла!')
    return redirect(url_for('uploaded_files'))

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)), debug=False)
