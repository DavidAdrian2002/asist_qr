from flask import Flask, render_template, request, redirect, jsonify, send_file
from utils.db import init_db, get_connection
import uuid
from utils.qr_generator import generar_qr
from datetime import datetime
from openpyxl import Workbook
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash

@app.before_request
def inicializar_db():
    if not hasattr(app, "db_initialized"):
        init_db()
        app.db_initialized = True
app = Flask(__name__)
app.secret_key = "clave_super_secreta_123"

# asistencia_activa = True
# curso_actual = None
# session_id_actual = None  # 🔥 NUEVO

from flask import session

@app.before_request
def proteger_rutas():

    rutas_libres = ["/login", "/register"]

    if request.path in rutas_libres:
        return

    if not session.get("docente_id"):
        return redirect("/login")

# ================== LOGIN ==================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        conn = get_connection()

        docente = conn.execute("""
            SELECT * FROM docentes WHERE usuario = ?
        """, (usuario,)).fetchone()

        conn.close()

        if docente and check_password_hash(docente["password"], password):

            session["docente_id"] = docente["id"]

            return redirect("/")

        return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")


# ================== REGISTER ==================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        hash_password = generate_password_hash(password)

        conn = get_connection()

        try:
            conn.execute("""
                INSERT INTO docentes (usuario, password)
                VALUES (?, ?)
            """, (usuario, hash_password))
            conn.commit()
        except:
            conn.close()
            return render_template("register.html", error="Usuario ya existe")

        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ================== LOGOUT ==================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
# ------------------ INICIO ------------------

@app.route("/")
def index():
    return render_template("index.html")

# ------------------ ESCUELAS ------------------

@app.route("/escuelas")
def escuelas():
    docente_id = session.get("docente_id")

    conn = get_connection()
    escuelas = conn.execute(
        "SELECT * FROM escuelas WHERE docente_id = ?",
        (docente_id,)
    ).fetchall()
    conn.close()

    return render_template("escuelas.html", escuelas=escuelas)

@app.route("/add_escuela", methods=["POST"])
def add_escuela():
    nombre = request.form["nombre"]
    docente_id = session.get("docente_id")

    conn = get_connection()
    conn.execute(
        "INSERT INTO escuelas (nombre, docente_id) VALUES (?, ?)",
        (nombre, docente_id)
    )
    conn.commit()
    conn.close()

    return redirect("/escuelas")

@app.route("/delete_escuela/<int:id>")
def delete_escuela(id):
    conn = get_connection()
    conn.execute("DELETE FROM escuelas WHERE id = ?", (id,))
    conn.execute("DELETE FROM cursos WHERE escuela_id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/escuelas")

@app.route("/edit_escuela/<int:id>", methods=["GET", "POST"])
def edit_escuela(id):
    conn = get_connection()

    if request.method == "POST":
        nombre = request.form["nombre"]
        conn.execute("UPDATE escuelas SET nombre = ? WHERE id = ?", (nombre, id))
        conn.commit()
        conn.close()
        return redirect("/escuelas")

    escuela = conn.execute("SELECT * FROM escuelas WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template("edit_escuela.html", escuela=escuela)

@app.route("/cursos_por_escuela/<int:escuela_id>")
def cursos_por_escuela(escuela_id):
    conn = get_connection()

    cursos = conn.execute("""
        SELECT * FROM cursos WHERE escuela_id = ?
    """, (escuela_id,)).fetchall()

    conn.close()

    return jsonify([dict(c) for c in cursos])

# ------------------ CURSOS ------------------

@app.route("/cursos")
def cursos():
    docente_id = session.get("docente_id")

    conn = get_connection()

    cursos = conn.execute("""
        SELECT 
            cursos.id, 
            cursos.nombre, 
            cursos.docente,
            escuelas.nombre as escuela
        FROM cursos
        JOIN escuelas ON cursos.escuela_id = escuelas.id
        WHERE cursos.docente_id = ?
    """, (docente_id,)).fetchall()

    escuelas = conn.execute(
        "SELECT * FROM escuelas WHERE docente_id = ?",
        (docente_id,)
    ).fetchall()

    conn.close()

    return render_template("cursos.html", cursos=cursos, escuelas=escuelas)

@app.route("/add_curso", methods=["POST"])
def add_curso():
    nombre = request.form["nombre"]
    escuela_id = request.form["escuela_id"]
    docente = request.form["docente"]
    docente_id = session.get("docente_id")

    if not escuela_id:
        return redirect("/cursos")

    conn = get_connection()
    conn.execute(
        "INSERT INTO cursos (nombre, escuela_id, docente, docente_id) VALUES (?, ?, ?, ?)",
        (nombre, escuela_id, docente, docente_id)
    )
    conn.commit()
    conn.close()

    return redirect("/cursos")

# ------------------ ALUMNOS ------------------

@app.route("/alumnos")
def alumnos():
    docente_id = session.get("docente_id")

    conn = get_connection()

    alumnos = conn.execute("""
    SELECT alumnos.*, 
           cursos.nombre AS curso,
           cursos.escuela_id,
           escuelas.nombre AS escuela
    FROM alumnos
    LEFT JOIN cursos ON alumnos.curso_id = cursos.id
    LEFT JOIN escuelas ON cursos.escuela_id = escuelas.id
    WHERE alumnos.docente_id = ?
    ORDER BY escuelas.nombre, cursos.nombre
    """, (docente_id,)).fetchall()

    cursos = conn.execute(
        "SELECT * FROM cursos WHERE docente_id = ?",
        (docente_id,)
    ).fetchall()

    escuelas = conn.execute(
        "SELECT * FROM escuelas WHERE docente_id = ?",
        (docente_id,)
    ).fetchall()

    conn.close()

    return render_template("alumnos.html", alumnos=alumnos, cursos=cursos, escuelas=escuelas)

@app.route("/add_alumno", methods=["POST"])
def add_alumno():
    nombre = request.form["nombre"]
    apellido = request.form["apellido"]
    dni = request.form["dni"]
    sexo = request.form["sexo"]
    curso_id = request.form["curso_id"]
    docente_id = session.get("docente_id")

    qr_code = str(uuid.uuid4())
    generar_qr(qr_code, qr_code, nombre, apellido, dni)

    conn = get_connection()
    conn.execute("""
        INSERT INTO alumnos (nombre, apellido, dni, sexo, curso_id, qr_code, docente_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (nombre, apellido, dni, sexo, curso_id, qr_code, docente_id))

    conn.commit()
    conn.close()

    return redirect("/alumnos")

@app.route("/imprimir_qr_escuela/<int:escuela_id>")
def imprimir_qr_escuela(escuela_id):

    docente_id = session.get("docente_id")

    conn = get_connection()

    alumnos = conn.execute("""
        SELECT alumnos.*, cursos.nombre AS curso
        FROM alumnos
        JOIN cursos ON alumnos.curso_id = cursos.id
        WHERE cursos.escuela_id = ?
        AND alumnos.docente_id = ?
    """, (escuela_id, docente_id)).fetchall()

    escuela = conn.execute(
        "SELECT * FROM escuelas WHERE id = ? AND docente_id = ?",
        (escuela_id, docente_id)
    ).fetchone()

    conn.close()

    return render_template(
        "imprimir_qr_escuela.html",
        alumnos=alumnos,
        escuela=escuela
    )

@app.route("/registrar_asistencia", methods=["POST"])
def registrar_asistencia():

    # 🧠 obtener datos de sesión
    activa = session.get("activa")
    session_id = session.get("session_id")

    # 🔒 validar estado
    if not activa:
        return jsonify({"success": False, "error": "Asistencia no activa"})

    if not session_id:
        return jsonify({"success": False, "error": "Sesión no iniciada"})

    data = request.get_json()
    qr = data.get("qr")
    curso_id = data.get("curso_id")

    if not qr or not curso_id:
        return jsonify({"success": False, "error": "Datos incompletos"})

    conn = get_connection()

    # 🔍 buscar alumno
    alumno = conn.execute("""
        SELECT * FROM alumnos 
        WHERE qr_code = ? AND curso_id = ?
    """, (qr, curso_id)).fetchone()

    if not alumno:
        conn.close()
        return jsonify({"success": False, "error": "Alumno no encontrado"})

    hoy = datetime.now().strftime("%Y-%m-%d")
    hora = datetime.now().strftime("%H:%M:%S")

    # 🔥 evitar duplicados en ESTA sesión
    existe = conn.execute("""
        SELECT * FROM asistencias
        WHERE alumno_id = ? 
        AND fecha = ? 
        AND session_id = ?
    """, (alumno["id"], hoy, session_id)).fetchone()

    if not existe:
        conn.execute("""
            INSERT INTO asistencias (alumno_id, fecha, estado, hora, session_id)
            VALUES (?, ?, 'presente', ?, ?)
        """, (alumno["id"], hoy, hora, session_id))
        conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "nombre": alumno["nombre"],
        "apellido": alumno["apellido"],
        "dni": alumno["dni"],
        "sexo": alumno["sexo"]
    })
# ------------------ ESCÁNER ------------------

@app.route("/escaner/<int:curso_id>")
def escaner(curso_id):

    # 🧠 guardar datos en sesión (por usuario)
    session["curso_id"] = curso_id
    session["activa"] = True
    session["session_id"] = str(uuid.uuid4())

    return render_template("escaner.html", curso_id=curso_id)

@app.route("/seleccionar_curso")
def seleccionar_curso():
    conn = get_connection()
    cursos = conn.execute("""
        SELECT cursos.id, cursos.nombre, escuelas.nombre AS escuela
        FROM cursos
        JOIN escuelas ON cursos.escuela_id = escuelas.id
    """).fetchall()
    conn.close()

    return render_template("seleccionar_curso.html", cursos=cursos)

# ------------------ REGISTRAR ASISTENCIA TARDE ------------------

@app.route("/registrar_tarde", methods=["POST"])
def registrar_tarde():

    # 🧠 obtener datos de sesión
    session_id = session.get("session_id")

    data = request.get_json()
    qr = data.get("qr")
    curso_id = data.get("curso_id")

    # 🔒 validaciones básicas
    if not qr or not curso_id:
        return jsonify({"success": False, "error": "Datos incompletos"})

    if not session_id:
        return jsonify({"success": False, "error": "Sesión no iniciada"})

    conn = get_connection()

    # 🔍 buscar alumno (IMPORTANTE: solo por QR primero)
    alumno = conn.execute("""
        SELECT * FROM alumnos 
        WHERE qr_code = ?
    """, (qr,)).fetchone()

    if not alumno:
        conn.close()
        return jsonify({"success": False, "error": "QR no registrado"})

    # 🔒 validar que pertenece al curso
    if alumno["curso_id"] != int(curso_id):
        conn.close()
        return jsonify({"success": False, "error": "Alumno no pertenece a este curso"})

    hoy = datetime.now().strftime("%Y-%m-%d")
    hora = datetime.now().strftime("%H:%M:%S")

    # 🔍 buscar si ya existe en ESTA sesión
    existe = conn.execute("""
        SELECT * FROM asistencias
        WHERE alumno_id = ?
        AND fecha = ?
        AND session_id = ?
    """, (alumno["id"], hoy, session_id)).fetchone()

    if existe:
        # 🔁 actualizar a tarde
        conn.execute("""
            UPDATE asistencias
            SET estado = 'tarde', hora = ?
            WHERE alumno_id = ?
            AND fecha = ?
            AND session_id = ?
        """, (hora, alumno["id"], hoy, session_id))
    else:
        # 🆕 insertar directamente como tarde
        conn.execute("""
            INSERT INTO asistencias (alumno_id, fecha, estado, hora, session_id)
            VALUES (?, ?, 'tarde', ?, ?)
        """, (alumno["id"], hoy, hora, session_id))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "nombre": alumno["nombre"],
        "apellido": alumno["apellido"],
        "estado": "tarde"
    })

# from flask import session, redirect, render_template

@app.route("/afh")
def afh():

    # 🧠 obtener datos de sesión
    curso_id = session.get("curso_id")
    session_id = session.get("session_id")

    # 🔒 validar sesión activa
    if not curso_id or not session_id:
        return redirect("/")

    return render_template("afh.html", curso_id=curso_id)

@app.route("/cerrar_jornada")
def cerrar_jornada():

    # 🧠 obtener datos de sesión
    curso_id = session.get("curso_id")
    session_id = session.get("session_id")

    if not curso_id or not session_id:
        return redirect("/")

    conn = get_connection()
    hoy = datetime.now().strftime("%Y-%m-%d")

    # 📊 obtener datos SOLO de esta sesión
    datos = conn.execute("""
        SELECT alumnos.nombre, alumnos.apellido, alumnos.dni, alumnos.sexo, asistencias.estado
        FROM asistencias
        JOIN alumnos ON alumnos.id = asistencias.alumno_id
        WHERE fecha = ?
        AND alumnos.curso_id = ?
        AND asistencias.session_id = ?
    """, (hoy, curso_id, session_id)).fetchall()

    conn.close()

    # 📄 crear Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Asistencia"

    ws.append(["Nombre", "Apellido", "DNI", "Sexo", "Estado"])

    for d in datos:
        ws.append([
            d["nombre"],
            d["apellido"],
            d["dni"],
            d["sexo"],
            d["estado"]
        ])

    # 🔥 nombre dinámico (muy recomendable)
    archivo = f"asistencia_{hoy}.xlsx"
    wb.save(archivo)

    # 🧹 limpiar sesión COMPLETA (esto reemplaza los globals)
    session.clear()

    # ⬇ descargar archivo
    return send_file(archivo, as_attachment=True)
# ------------------ RESULTADO ------------------

@app.route("/resultado/<int:curso_id>")
def resultado(curso_id):

    # 🧠 obtener sesión del usuario
    session_id = session.get("session_id")
    curso_sesion = session.get("curso_id")

    # 🔒 validación fuerte
    if not session_id or not curso_sesion:
        return redirect("/")

    # 🚫 evitar que cambien el curso por URL
    if curso_id != curso_sesion:
        return redirect(f"/resultado/{curso_sesion}")

    conn = get_connection()
    hoy = datetime.now().strftime("%Y-%m-%d")

    # ✅ presentes SOLO de ESTA sesión
    presentes = conn.execute("""
        SELECT alumnos.*, asistencias.estado
        FROM asistencias
        JOIN alumnos ON alumnos.id = asistencias.alumno_id
        WHERE fecha = ? 
        AND alumnos.curso_id = ?
        AND asistencias.session_id = ?
    """, (hoy, curso_id, session_id)).fetchall()

    # ✅ todos los alumnos del curso
    todos = conn.execute("""
        SELECT * FROM alumnos WHERE curso_id = ?
    """, (curso_id,)).fetchall()

    # ✅ calcular ausentes correctamente
    presentes_ids = [p["id"] for p in presentes]
    ausentes = [a for a in todos if a["id"] not in presentes_ids]

    conn.close()

    return render_template(
        "resultado.html",
        presentes=presentes,
        ausentes=ausentes
    )
# ------------------ EXPORTAR ------------------

@app.route("/exportar")
def exportar():

    # 🧠 obtener datos de sesión
    curso_id = session.get("curso_id")
    session_id = session.get("session_id")

    if not curso_id or not session_id:
        return redirect("/")

    conn = get_connection()
    hoy = datetime.now().strftime("%Y-%m-%d")

    datos = conn.execute("""
        SELECT alumnos.nombre, alumnos.apellido, alumnos.dni, alumnos.sexo, asistencias.estado
        FROM asistencias
        JOIN alumnos ON alumnos.id = asistencias.alumno_id
        WHERE fecha = ? 
        AND alumnos.curso_id = ?
        AND asistencias.session_id = ?
    """, (hoy, curso_id, session_id)).fetchall()

    conn.close()

    # 📄 crear Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Asistencia"

    ws.append(["Nombre", "Apellido", "DNI", "Sexo", "Estado"])

    for d in datos:
        ws.append([
            d["nombre"],
            d["apellido"],
            d["dni"],
            d["sexo"],
            d["estado"]
        ])

    # 🔥 nombre dinámico (evita sobrescribir)
    archivo = f"asistencia_{hoy}.xlsx"
    wb.save(archivo)

    return send_file(archivo, as_attachment=True)
# ------------------ FINALIZAR ------------------

@app.route("/finalizar")
def finalizar():

    curso_id = session.get("curso_id")

    if not curso_id:
        return redirect("/")

    # 🔒 cerrar asistencia
    session["activa"] = False

    return redirect(f"/resultado/{curso_id}")

# ------------------ MAIN ------------------

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)