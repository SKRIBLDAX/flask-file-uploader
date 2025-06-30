import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash, session
from functools import wraps

UPLOAD_FOLDER = 'uploads'
ADMIN_USERNAME = 'SKRIBLDAX'
ADMIN_PASSWORD = 'kakawka2281337'  # Задайте свой пароль

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'supersecretkey'  # Для сессий и flash-сообщений

def allowed_file(filename):
    return filename != ''

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('Вы вошли как администратор!')
            return redirect(url_for('upload_file'))
        else:
            flash('Неверный логин или пароль!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    flash('Вы вышли из аккаунта администратора.')
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
            flash('Файл успешно загружен')
            return redirect(url_for('uploaded_files'))
    return render_template('upload.html')

@app.route('/files')
@login_required
def uploaded_files():
    files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        files = os.listdir(app.config['UPLOAD_FOLDER'])
    is_admin = session.get('is_admin', False)
    return render_template('files.html', files=files, is_admin=is_admin)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_file(filename):
    if not session.get('is_admin'):
        flash('Нет доступа для удаления файла!')
        return redirect(url_for('uploaded_files'))
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f'Файл {filename} удалён')
    else:
        flash('Файл не найден')
    return redirect(url_for('uploaded_files'))

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)), debug=False)
