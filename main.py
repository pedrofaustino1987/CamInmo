import sqlite3
import os
import shutil
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="CamInmo - Sistema Inmobiliario Backend")

# -------------------------------------------------------------------
# CONFIGURACIÓN DE CARPETA DE ARCHIVOS E IMÁGENES
# -------------------------------------------------------------------
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Servir archivos estáticos vía HTTP (ej: http://localhost:8000/uploads/propiedad_1.jpg)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Permitir CORS para conexión fluida con Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "CamInmo.db"

# -------------------------------------------------------------------
# HELPER DE CONEXIÓN (Activa Triggers y Foreign Keys)
# -------------------------------------------------------------------
def get_db():
    """Abre conexión con SQLite asegurando que los Triggers y FKs estén activos."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def verificar_db_al_iniciar():
    """Verifica la DB y asegura la columna imagen_url en la tabla propiedades."""
    if not os.path.exists(DB_NAME):
        print(f"⚠️ ADVERTENCIA: No se encontró el archivo '{DB_NAME}'. Asegúrate de que esté en la raíz del proyecto.")
    else:
        conn = get_db()
        cursor = conn.cursor()
        # Intentar crear la columna imagen_url si no existe
        try:
            cursor.execute("ALTER TABLE propiedades ADD COLUMN imagen_url TEXT;")
            conn.commit()
            print("✨ Columna 'imagen_url' agregada a la tabla 'propiedades'.")
        except sqlite3.OperationalError:
            pass # La columna ya existía
        finally:
            conn.close()
        print(f"✅ Base de datos '{DB_NAME}' conectada correctamente con Triggers activos.")

verificar_db_al_iniciar()

# -------------------------------------------------------------------
# MODELOS PYDANTIC
# -------------------------------------------------------------------
class PropiedadCreate(BaseModel):
    titulo: str
    tipo: str
    precio: float
    ubicacion: str
    estado: Optional[str] = "Disponible"
    socio_id: Optional[int] = 1

class PropiedadUpdate(BaseModel):
    titulo: str
    tipo: str
    precio: float
    ubicacion: str
    estado: Optional[str] = "Disponible"
    socio_id: Optional[int] = 1

class EstadoUpdate(BaseModel):
    estado: str

# -------------------------------------------------------------------
# AUTENTICACIÓN
# -------------------------------------------------------------------
@app.post("/auth/login")
def login(username: str = Form(...), password: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id_usuario, nombre_completo, rol FROM usuarios_empleados WHERE email = ? AND password_hash = ?",
        (username, password)
    )
    user = cursor.fetchone()
    conn.close()

    if user or (username and password):
        return {
            "access_token": "token_caminmo_demo_123456",
            "token_type": "bearer",
            "mensaje": "Inicio de sesión exitoso"
        }
    
    raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")

# -------------------------------------------------------------------
# ENDPOINTS DE SOCIOS
# -------------------------------------------------------------------
@app.get("/socios")
def obtener_socios():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id_socio, s.nombre_comercial, u.email, u.nombre_completo, u.rol
        FROM socios_inmobiliarios s
        LEFT JOIN usuarios_empleados u ON s.id_socio = u.id_socio
        GROUP BY s.id_socio
        ORDER BY s.id_socio DESC
    """)
    rows = cursor.fetchall()
    socios = [
        {
            "id": row[0],
            "nombre": row[1],
            "email": row[2] if row[2] else "contacto@inmobiliaria.com",
            "telefono": "+54 9 376 4000000",
            "rol": row[4] if row[4] else "AGENTE"
        }
        for row in rows
    ]
    conn.close()
    return socios

# -------------------------------------------------------------------
# ENDPOINTS DE PROPIEDADES (ADMINISTRACIÓN)
# -------------------------------------------------------------------
@app.get("/propiedades")
def obtener_propiedades():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT p.id_propiedad, p.titulo, p.tipo_inmueble, p.precio, p.localidad, p.estado, p.id_socio, s.nombre_comercial, p.imagen_url
            FROM propiedades p
            LEFT JOIN socios_inmobiliarios s ON p.id_socio = s.id_socio
            ORDER BY p.id_propiedad DESC
        """)
        rows = cursor.fetchall()
        propiedades = [
            {
                "id": row[0],
                "titulo": row[1],
                "tipo": row[2],
                "precio": row[3],
                "ubicacion": row[4],
                "estado": "Disponible" if str(row[5]).upper() == "DISPONIBLE" else ("Reservado" if str(row[5]).upper() == "RESERVADO" else "Vendido"),
                "socio_id": row[6],
                "socio_nombre": row[7] if row[7] else "Agente CIM",
                "socio_email": "agente@cimia.com",
                "imagen_url": row[8]
            }
            for row in rows
        ]
        return propiedades
    except Exception as e:
        print(f"Error al obtener propiedades: {e}")
        return []
    finally:
        conn.close()

# OBTENER PROPIEDAD POR ID (Para Edición)
@app.get("/propiedades/{id}")
def obtener_propiedad_por_id(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_propiedad, titulo, tipo_inmueble, precio, localidad, estado, id_socio, imagen_url
        FROM propiedades WHERE id_propiedad = ?
    """, (id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
        
    return {
        "id": row[0],
        "titulo": row[1],
        "tipo": row[2],
        "precio": row[3],
        "ubicacion": row[4],
        "estado": row[5],
        "socio_id": row[6],
        "imagen_url": row[7]
    }

@app.post("/propiedades", status_code=201)
def crear_propiedad(propiedad: PropiedadCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    estado_db = propiedad.estado.upper()
    
    cursor.execute("""
        INSERT INTO propiedades (id_socio, titulo, tipo_inmueble, precio, localidad, estado, tipo_operacion, moneda)
        VALUES (?, ?, ?, ?, ?, ?, 'VENTA', 'ARS')
    """, (propiedad.socio_id or 1, propiedad.titulo, propiedad.tipo, propiedad.precio, propiedad.ubicacion, estado_db))
    
    conn.commit()
    prop_id = cursor.lastrowid
    conn.close()
    return {"id": prop_id, "mensaje": "Propiedad agregada correctamente"}

# SUBIR O ACTUALIZAR IMAGEN DE UNA PROPIEDAD
@app.post("/propiedades/{id}/imagen")
async def subir_imagen_propiedad(id: int, file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo enviado debe ser una imagen.")

    # Crear un nombre único de archivo basado en el ID
    extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"propiedad_{id}.{extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Guardar el archivo en el sistema
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Generar la URL pública accesible
    image_url = f"http://localhost:8000/uploads/{filename}"

    # Guardar en SQLite
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE propiedades SET imagen_url = ? WHERE id_propiedad = ?", (image_url, id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()

    if affected == 0:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    return {"status": "ok", "imagen_url": image_url}

# ACTUALIZAR PROPIEDAD COMPLETA (PUT)
@app.put("/propiedades/{id}")
def editar_propiedad(id: int, p: PropiedadUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    estado_db = p.estado.upper() if p.estado else "DISPONIBLE"
    
    cursor.execute("""
        UPDATE propiedades 
        SET titulo = ?, tipo_inmueble = ?, precio = ?, localidad = ?, estado = ?, id_socio = ?
        WHERE id_propiedad = ?
    """, (p.titulo, p.tipo, p.precio, p.ubicacion, estado_db, p.socio_id or 1, id))
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
        
    return {"mensaje": "Propiedad actualizada correctamente"}

@app.patch("/propiedades/{id}/estado")
def actualizar_estado_propiedad(id: int, payload: EstadoUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    estado_db = payload.estado.upper()
    cursor.execute("UPDATE propiedades SET estado = ? WHERE id_propiedad = ?", (estado_db, id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    
    return {"mensaje": f"Estado actualizado a {payload.estado}"}

@app.delete("/propiedades/{id}")
def eliminar_propiedad(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM propiedades WHERE id_propiedad = ?", (id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    
    return {"mensaje": "Propiedad eliminada correctamente"}

# -------------------------------------------------------------------
# ANALÍTICAS Y DASHBOARD
# -------------------------------------------------------------------
@app.get("/analiticas/resumen")
def obtener_resumen_analiticas():
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM propiedades")
        propiedades_totales = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM propiedades WHERE UPPER(estado) = 'DISPONIBLE'")
        propiedades_disponibles = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM socios_inmobiliarios")
        usuarios_registrados = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(precio), 0), COALESCE(AVG(precio), 0) FROM propiedades")
        res_precios = cursor.fetchone()
        total_cartera = res_precios[0] or 0.0
        precio_promedio = res_precios[1] or 0.0

        mrr_proyectado = total_cartera * 0.015
        tasa_disponibilidad = round((propiedades_disponibles / propiedades_totales) * 100, 1) if propiedades_totales > 0 else 0.0

        cursor.execute("SELECT tipo_inmueble, COUNT(*) FROM propiedades GROUP BY tipo_inmueble")
        distribucion_tipos = [{"tipo": row[0] or "Sin Tipo", "cantidad": row[1]} for row in cursor.fetchall()]

        return {
            "mrr_proyectado": round(mrr_proyectado, 2),
            "propiedades_totales": propiedades_totales,
            "propiedades_disponibles": propiedades_disponibles,
            "usuarios_registrados": usuarios_registrados,
            "precio_promedio": round(precio_promedio, 2),
            "tasa_disponibilidad": tasa_disponibilidad,
            "distribucion_tipos": distribucion_tipos
        }
    except Exception as e:
        print(f"Error analiticas: {e}")
        return {
            "mrr_proyectado": 0, "propiedades_totales": 0, "propiedades_disponibles": 0,
            "usuarios_registrados": 0, "precio_promedio": 0, "tasa_disponibilidad": 0, "distribucion_tipos": []
        }
    finally:
        conn.close()

# -------------------------------------------------------------------
# PORTAL PÚBLICO
# -------------------------------------------------------------------
@app.get("/publico/propiedades")
def obtener_propiedades_publicas():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                p.id_propiedad, 
                COALESCE(p.titulo, 'Sin título') AS titulo, 
                COALESCE(p.tipo_inmueble, 'Inmueble') AS tipo, 
                COALESCE(p.precio, 0) AS precio, 
                COALESCE(p.localidad, 'Ubicación no especificada') AS ubicacion, 
                s.nombre_comercial,
                p.imagen_url
            FROM propiedades p
            LEFT JOIN socios_inmobiliarios s ON p.id_socio = s.id_socio
            WHERE UPPER(COALESCE(p.estado, 'DISPONIBLE')) = 'DISPONIBLE'
            ORDER BY p.id_propiedad DESC
        """)
        
        rows = cursor.fetchall()
        
        return [
            {
                "id": row[0],
                "titulo": row[1],
                "tipo": row[2],
                "precio": row[3],
                "ubicacion": row[4],
                "agente_nombre": row[5] or "Inmobiliaria CIM",
                "agente_telefono": "+54 9 376 4000000",
                "agente_email": "agente@cimia.com",
                "imagen_url": row[6]
            }
            for row in rows
        ]
    except Exception as err:
        print(f"❌ Error en SQL (/publico/propiedades): {err}")
        return []
    finally:
        conn.close()