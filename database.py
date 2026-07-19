import sqlite3
from contextlib import contextmanager

DATABASE_NAME = "CamInmo.db"

@contextmanager
def get_db_connection():
    """
    Genera un administrador de contexto para asegurar que la conexión
    a la base de datos se abra y se cierre correctamente en cada petición.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    # Habilitamos el soporte de claves foráneas para que los triggers funcionen
    conn.execute("PRAGMA foreign_keys = ON;")
    # Permite acceder a las columnas por su nombre de texto como un diccionario
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()