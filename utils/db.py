import sqlite3

DB_PATH = "database/db.sqlite3"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # DOCENTES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS docentes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # ESCUELAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS escuelas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        docente_id INTEGER,
        FOREIGN KEY(docente_id) REFERENCES docentes(id) ON DELETE CASCADE
    )
    """)

    # CURSOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        docente TEXT,
        escuela_id INTEGER,
        docente_id INTEGER,
        FOREIGN KEY(escuela_id) REFERENCES escuelas(id) ON DELETE CASCADE,
        FOREIGN KEY(docente_id) REFERENCES docentes(id) ON DELETE CASCADE
    )
    """)

    # ALUMNOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alumnos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        dni TEXT,
        sexo TEXT,
        curso_id INTEGER,
        qr_code TEXT,
        docente_id INTEGER,
        FOREIGN KEY(curso_id) REFERENCES cursos(id) ON DELETE CASCADE,
        FOREIGN KEY(docente_id) REFERENCES docentes(id) ON DELETE CASCADE,
        UNIQUE(dni, docente_id)
    )
    """)

    # ASISTENCIAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asistencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alumno_id INTEGER,
        fecha TEXT,
        estado TEXT,
        hora TEXT,
        session_id TEXT,
        docente_id INTEGER,
        FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
        FOREIGN KEY(docente_id) REFERENCES docentes(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()