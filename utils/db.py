import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("postgresql://asistencia_db_4etu_user:fWGISPPJQ4LAng6ZHYDxDAeL3QNyzG9G@dpg-d7od29l8nd3s738rj9i0-a/asistencia_db_4etu")

def get_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ================== TABLA DOCENTES ==================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS docentes (
        id SERIAL PRIMARY KEY,
        usuario TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # ================== TABLA ESCUELAS ==================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS escuelas (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        docente_id INTEGER REFERENCES docentes(id)
    )
    """)

    # ================== TABLA CURSOS ==================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cursos (
        id SERIAL PRIMARY KEY,
        nombre TEXT,
        docente TEXT,
        escuela_id INTEGER REFERENCES escuelas(id),
        docente_id INTEGER REFERENCES docentes(id)
    )
    """)

    # ================== TABLA ALUMNOS ==================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alumnos (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        dni TEXT UNIQUE,
        sexo TEXT,
        curso_id INTEGER REFERENCES cursos(id),
        qr_code TEXT,
        docente_id INTEGER REFERENCES docentes(id)
    )
    """)

    # ================== TABLA ASISTENCIAS ==================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asistencias (
        id SERIAL PRIMARY KEY,
        alumno_id INTEGER REFERENCES alumnos(id),
        fecha TEXT,
        estado TEXT,
        hora TEXT,
        session_id TEXT
    )
    """)

    conn.commit()
    conn.close()