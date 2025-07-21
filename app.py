from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
import csv
import io
from datetime import datetime
from flask import send_from_directory


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

@app.route('/static/<path:filename>')
def serve_static(filename): 
        return send_from_directory('static', filename)

@app.route('/generar_pdf')
def generar_pdf():
    # Obtener datos de la base de datos
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM contactos ORDER BY id DESC;")
    contactos = cur.fetchall()
    cur.close()
    conn.close()
    
    # Crear buffer para el PDF
    buffer = io.BytesIO()
    
    # Configurar documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1))
    styles.add(ParagraphStyle(name='Right', alignment=2))
    
    # Color institucional CDMX
    color_guinda = colors.HexColor('#9c1d2b')
    color_fondo = colors.HexColor('#f5e6e8')
    
    # Encabezado con logos (reemplaza con rutas reales)
    try:
        # En la función generar_pdf
        logo1 = Image('static/logo1.png', width=1.5*inch, height=1*inch)
        logo2 = Image('static/logo2.png', width=1.5*inch, height=1*inch)
        elements.append(logo1)
        elements.append(Spacer(1, 0.4*inch))
    except:
        pass
    
    # Título
    elements.append(Paragraph("Gobierno de la Ciudad de México", 
                            styles["Title"]))
    elements.append(Paragraph("Registro de Contactos", 
                            styles["Heading1"]))
    elements.append(Spacer(1, 12))
    
    # Fecha de generación
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    elements.append(Paragraph(f"<b>Generado el:</b> {fecha}", 
                            styles["Normal"]))
    elements.append(Spacer(1, 24))
    
    # Tabla de contactos
    if contactos:
        # Encabezados de tabla
        data = [["ID", "Nombre", "Correo", "Teléfono"]]
        
        # Agregar filas de datos
        for contacto in contactos:
            data.append([
                str(contacto[0]),
                contacto[1],
                contacto[2],
                contacto[3]
            ])
        
        # Crear tabla
        tabla = Table(data)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), color_guinda),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), color_fondo),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(tabla)
    else:
        elements.append(Paragraph("No hay contactos registrados", 
                                styles["Heading2"]))
    
    elements.append(Spacer(1, 36))
    
    # Pie de página
    elements.append(Paragraph("© 2025 Gobierno de la Ciudad de México - Todos los derechos reservados", 
                            styles["Normal"]))
    
    # Construir PDF
    doc.build(elements)
    
    # Preparar para descarga
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, 
                   download_name='contactos_cdmx.pdf', 
                   mimetype='application/pdf')

@app.route('/generar_csv')
def generar_csv():
    # Obtener datos de la base de datos
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM contactos ORDER BY id DESC;")
    contactos = cur.fetchall()
    cur.close()
    conn.close()
    
    # Crear un buffer en memoria para el CSV
    buffer = io.StringIO()  # Asegúrate de tener esta línea
    
    # Crear escritor CSV
    writer = csv.writer(buffer)
    
    # Escribir encabezados con estilo institucional
    writer.writerow(["Reporte de Contactos - Gobierno de la Ciudad de México"])
    writer.writerow([])  # Línea vacía
    writer.writerow(["Generado el:", datetime.now().strftime("%d/%m/%Y %H:%M:%S")])
    writer.writerow([])  # Línea vacía
    writer.writerow(["ID", "Nombre", "Correo", "Teléfono"])
    
    # Escribir datos
    for contacto in contactos:
        writer.writerow(contacto)  # 'w' minúscula
    
    # Escribir pie de página
    writer.writerow([])  # Línea vacía
    writer.writerow(["© 2025Gobierno de la Ciudad de México - Todos los derechos reservados"])
    
    # Preparar para descarga
    buffer.seek(0)
    csv_data = buffer.getvalue()
    buffer.close()
    
    # Crear respuesta con el CSV
    response = app.response_class(
        response=csv_data,  # Corregido: = en lugar de -
        mimetype='text/csv',
    )
    response.headers.set("Content-Disposition", "attachment", filename="contactos_cdmx.csv")
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)