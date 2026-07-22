import sqlite3
import os

# Rutas de las bases de datos en la carpeta raíz
DB_PRINCIPAL = "CamInmo.db"
DB_SECUNDARIA = "cimia.db"

def fusionar_bases_de_datos():
    if not os.path.exists(DB_PRINCIPAL) or not os.path.exists(DB_SECUNDARIA):
        print("❌ Error: No se encontraron los archivos de base de datos.")
        return

    print(f"🚀 Iniciando fusión de '{DB_SECUNDARIA}' hacia '{DB_PRINCIPAL}'...")

    # Conexión a la base principal
    conn = sqlite3.connect(DB_PRINCIPAL)
    cursor = conn.cursor()

    try:
        # 1. Adjuntar la base cimia.db bajo el alias 'db_origen'
        cursor.execute(f"ATTACH DATABASE '{DB_SECUNDARIA}' AS db_origen;")

        # 2. Obtener todas las tablas existentes en cimia.db
        cursor.execute("SELECT name, sql FROM db_origen.sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tablas_origen = cursor.fetchall()

        for nombre_tabla, sql_creacion in tablas_origen:
            print(f"📦 Procesando tabla: '{nombre_tabla}'...")

            # Crear la tabla en CamInmo.db si aún no existe
            cursor.execute(sql_creacion.replace(f"CREATE TABLE {nombre_tabla}", f"CREATE TABLE IF NOT EXISTS {nombre_tabla}"))

            # Copiar todos los datos ignorando duplicados si hay conflictos de ID
            cursor.execute(f"INSERT OR IGNORE INTO {nombre_tabla} SELECT * FROM db_origen.{nombre_tabla};")

        # 3. Guardar cambios y desadjuntar
        conn.commit()
        cursor.execute("DETACH DATABASE db_origen;")
        print("✅ ¡Fusión completada con éxito! Todos los datos de 'cimia.db' están ahora dentro de 'CamInmo.db'.")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error durante el proceso de migración: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fusionar_bases_de_datos()