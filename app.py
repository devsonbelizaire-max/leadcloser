import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-leadcloser")

# Configuración de conexión a Supabase / PostgreSQL
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, email, password_hash):
        self.id = id
        self.email = email
        self.password_hash = password_hash

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if user_data:
        return User(id=user_data['id'], email=user_data['email'], password_hash=user_data['password'])
    return None

# --- RUTAS DE LA APLICACIÓN ---

# Página Principal / Dashboard
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        nome = request.form.get('nome')
        whatsapp = request.form.get('whatsapp')
        imovel = request.form.get('imovel')
        observacoes = request.form.get('observacoes')
        status = request.form.get('status', 'Novo')

        cursor.execute(
            "INSERT INTO leads (nome, whatsapp, imovel, observacoes, status, user_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (nome, whatsapp, imovel, observacoes, status, current_user.id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))

    # Obtener leads del usuario actual
    cursor.execute("SELECT * FROM leads WHERE user_id = %s ORDER BY id DESC", (current_user.id,))
    leads = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('index.html', leads=leads)

# Ruta para actualizar el Status del Lead
@app.route('/update_status/<int:lead_id>', methods=['POST'])
@login_required
def update_status(lead_id):
    new_status = request.form.get('status')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leads SET status = %s WHERE id = %s AND user_id = %s",
        (new_status, lead_id, current_user.id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

# Autenticación: Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data and check_password_hash(user_data['password'], password):
            user = User(id=user_data['id'], email=user_data['email'], password_hash=user_data['password'])
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('E-mail ou senha incorretos.')

    return render_template('login.html')

# Autenticación: Registro de Usuario
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_password))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('login'))
        except Exception:
            conn.rollback()
            cursor.close()
            conn.close()
            flash('Este e-mail já está cadastrado.')

    return render_template('register.html')

# Autenticación: Cerrar Sesión
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)