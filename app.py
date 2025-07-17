from flask import Flask, render_template, request, redirect, url_for
import psycopg2

app = Flask(__name__)

# Configuración de PostgreSQL
DB_CONFIG = {
    "dbname": "jcf_db",
    "user": "alx",
    "password": "1234",  # Cambiar contraseña
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

# Crear tabla si no existe
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS contactos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            correo VARCHAR(100) UNIQUE NOT NULL,
            telefono VARCHAR(20) NOT NULL
        );
        """)
        conn.commit()

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM contactos ORDER BY id DESC;")
    contactos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', contactos=contactos)

@app.route('/agregar', methods=['POST'])
def agregar():
    nombre = request.form['nombre']
    correo = request.form['correo']
    telefono = request.form['telefono']
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO contactos (nombre, correo, telefono) VALUES (%s, %s, %s)",
            (nombre, correo, telefono)
        )
        conn.commit()
    except psycopg2.IntegrityError:
        # Manejar error de correo duplicado
        pass
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/editar/<int:id>', methods=['POST'])
def editar(id):
    nuevo_nombre = request.form['nombre']
    nuevo_correo = request.form['correo']
    nuevo_telefono = request.form['telefono']
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE contactos SET nombre = %s, correo = %s, telefono = %s WHERE id = %s",
        (nuevo_nombre, nuevo_correo, nuevo_telefono, id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/eliminar/<int:id>')
def eliminar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM contactos WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
