import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave_secreta_para_sesiones')

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        hashed_pw = generate_password_hash(password)

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (email, hashed_pw))
            conn.commit()
            flash('¡Cuenta creada con éxito! Por favor inicia sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            flash('El correo ya está registrado o hubo un error.', 'danger')
        finally:
            cur.close()
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            return redirect(url_for('index'))
        else:
            flash('Correo o contraseña incorrectos.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        whatsapp = request.form['whatsapp']
        imovel = request.form['imovel']
        observacoes = request.form['observacoes']

        cur.execute(
            "INSERT INTO leads (nome, whatsapp, imovel, observacoes, user_id) VALUES (%s, %s, %s, %s, %s)",
            (nome, whatsapp, imovel, observacoes, user_id)
        )
        conn.commit()
        return redirect(url_for('index'))

    cur.execute("SELECT * FROM leads WHERE user_id = %s ORDER BY id DESC", (user_id,))
    leads = cur.fetchall()

    cur.close()
    conn.close()

    total_leads = len(leads)

    return render_template('index.html', leads=leads, total_leads=total_leads, email=session.get('user_email'))

if __name__ == '__main__':
    app.run(debug=True)
