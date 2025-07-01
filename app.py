import os
import json
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash, session
from functools import wraps
from werkzeug.utils import secure_filename
from datetime import datetime

UPLOAD_FOLDER = 'uploads'
USERS_FILE = 'users.json'
FILES_FILE = 'files.json'
ADMIN_USERNAME = 'Tim_Gaide'

AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, 'avatars')
ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'supersecretkey'

# ВРЕМЕННО: удаляем users.json при запуске, чтобы сбросить пользователей на сервере Render
if os.path.exists('users.json'):
    os.remove('users.json')

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

def allowed_avatar(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS

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
            users[username] = {"password": password}
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
        if username == ADMIN_USERNAME and users.get(ADMIN_USERNAME, {}).get('password') == password:
            session['username'] = username
            flash('Вы вошли как администратор!')
            return redirect(url_for('upload_file'))
        elif username in users and users[username].get('password') == password:
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
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            files = load_files()
            stat = os.stat(file_path)
            files[filename] = {
                'owner': session['username'],
                'size': stat.st_size,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            save_files(files)
            flash('Файл успешно загружен')
            return redirect(url_for('uploaded_files'))
    return render_template('upload.html')

@app.route('/files')
@login_required
def uploaded_files():
    files = load_files()
    files_info = []
    for fname, meta in files.items():
        if isinstance(meta, dict):
            files_info.append({
                'name': fname,
                'owner': meta.get('owner', ''),
                'size': meta.get('size', 0),
                'date': meta.get('date', '')
            })
        else:
            files_info.append({
                'name': fname,
                'owner': meta,
                'size': 0,
                'date': ''
            })
    is_admin_flag = is_admin()
    username = session.get('username')
    return render_template('files.html', files=files_info, is_admin=is_admin_flag, username=username)

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

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    users = load_users()
    username = session['username']
    user = users.get(username, {})
    avatar_url = user.get('avatar')
    if request.method == 'POST':
        # Загрузка аватара
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename and allowed_avatar(file.filename):
                filename = secure_filename(f"{username}_avatar.{file.filename.rsplit('.', 1)[1].lower()}")
                os.makedirs(AVATAR_FOLDER, exist_ok=True)
                file.save(os.path.join(AVATAR_FOLDER, filename))
                user['avatar'] = f"uploads/avatars/{filename}"
                users[username] = user
                save_users(users)
                flash('Аватар успешно обновлён!')
                return redirect(url_for('profile'))
            else:
                flash('Недопустимый формат аватара!')
        # Смена пароля
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if old_password and new_password and confirm_password:
            admin_password = users.get(ADMIN_USERNAME, {}).get('password')
            if username == ADMIN_USERNAME:
                correct_old = old_password == admin_password
            else:
                correct_old = user.get('password') == old_password
            if not correct_old:
                flash('Старый пароль неверен!')
            elif new_password != confirm_password:
                flash('Новые пароли не совпадают!')
            elif len(new_password) < 4:
                flash('Пароль слишком короткий!')
            else:
                users[username]['password'] = new_password
                save_users(users)
                flash('Пароль успешно изменён!')
                return redirect(url_for('profile'))
    return render_template('profile.html', avatar_url=avatar_url, username=username)

@app.route('/uploads/avatars/<filename>')
def avatar_file(filename):
    return send_from_directory(AVATAR_FOLDER, filename)

@app.route('/upload_ajax', methods=['POST'])
@login_required
def upload_ajax():
    if 'file' not in request.files:
        return {'success': False, 'message': 'Нет файла в запросе'}, 400
    file = request.files['file']
    if file.filename == '':
        return {'success': False, 'message': 'Файл не выбран'}, 400
    if file and allowed_file(file.filename):
        filename = file.filename
        if filename is None:
            return {'success': False, 'message': 'Некорректное имя файла'}, 400
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        files = load_files()
        stat = os.stat(file_path)
        files[filename] = {
            'owner': session['username'],
            'size': stat.st_size,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_files(files)
        return {'success': True, 'message': 'Файл успешно загружен'}, 200
    return {'success': False, 'message': 'Ошибка загрузки файла'}, 400

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)), debug=False)
