from flask import Flask, request, render_template, redirect, url_for, session, flash, send_file, render_template_string
import sqlite3
import subprocess
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from markupsafe import escape
import os

from config import UPLOAD_FOLDER, secret_key
from databases_functions import get_db_connection_users, get_db_connection_books, get_db_connection_reviews

app = Flask(__name__)

app.secret_key = secret_key
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def main_page():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection_users()
        query = "SELECT * FROM users WHERE name = ?"
        user = conn.execute(query, (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Пароли не совпадают!')
            return redirect(url_for('register'))

        conn = get_db_connection_users()
        existing_user = conn.execute('SELECT * FROM users WHERE name = ?', (username,)).fetchone()

        if existing_user:
            flash('Такой пользователь уже существует!', 'error')
            conn.close()
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        try:
            conn.execute('INSERT INTO users (name, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('Произошла ошибка, попробуйте снова.', 'error')
        finally:
            conn.close()

        return redirect(url_for('login'))

    return render_template('register_page.html')


@app.route('/home')
def home():
    if 'username' in session:
        conn = get_db_connection_books()
        books = conn.execute('SELECT * FROM books').fetchall()
        conn.close()
        return render_template('home.html', books=books)
    return redirect(url_for('login'))


@app.route('/view_cover')
def view_cover():
    cover_path = request.args.get('cover_path')
    if cover_path:
        safe_directory = os.path.abspath('uploads/')
        conn = get_db_connection_books()
        db_cover_filename = conn.execute('SELECT cover_path FROM books WHERE cover_path= ?', (cover_path,)).fetchone()
        conn.close()
        if not db_cover_filename:
            return 'Файл обложки не найден в базе данных'
        cover_path = os.path.abspath(os.path.join(safe_directory, cover_path))

        if not cover_path.startswith(safe_directory):
            return 'Недопустимый путь к обложке'

        try:
            return send_file(cover_path)
        except Exception as e:
            return str(e)

    return 'Путь к обложке не указан'

@app.route('/reviews')
def view_reviews():
    conn = get_db_connection_reviews()
    reviews = conn.execute('SELECT * FROM reviews').fetchall()
    conn.close()
    return render_template_string(open('templates/review_page.html').read(), reviews=reviews)


@app.route('/post_review', methods=['GET', 'POST'])
def post_review():
    conn = get_db_connection_reviews()
    if request.method == 'POST':
        book_title = escape(request.form['book_title'])
        review_text = escape(request.form['review'])
        conn.execute('INSERT INTO reviews (title, review) VALUES (?, ?)', 
                     (book_title, review_text))
        conn.commit()
        conn.close()
        return redirect(url_for('view_reviews'))

    return render_template_string(open('templates/review_page.html').read())


@app.route('/upload', methods=['GET', 'POST'])
def upload_book():
    if request.method == 'POST':
        book_title = request.form['title']
        author = request.form['author']
        file = request.files['file']
        filename = file.filename
        if file:
            try:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                filepath = os.path.join('uploads/', filename)
                cmd = ["convert", "-resize", "99%", os.path.join(app.config['UPLOAD_FOLDER'], filename), os.path.join(app.config['UPLOAD_FOLDER'], 'backup.jpg')]
                subprocess.check_call(cmd)
                conn = get_db_connection_books()
                conn.execute('INSERT INTO books (title, author, cover_path) VALUES (?, ?, ?)', 
                (book_title, author, filename))
                conn.commit()
                conn.close()
            except Exception as e:
                return 'Error: ' + str(e) 
        return redirect(url_for('home'))
    return render_template('upload_book.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
