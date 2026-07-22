from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3

app = FastAPI(title="CamInmo - Sistema Inmobiliario Backend")

# Permitir CORS para conexión fluida con Next.js (http://localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# CONFIGURACIÓN DE LA BASE DE DATOS
# -------------------------------------------------------------------
DB_NAME = "CamInmo.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabla de Socios / Agentes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS socios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            telefono TEXT,
            rol TEXT DEFAULT 'Agente'
        )
    """)

    # Tabla de Propiedades
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS propiedades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            tipo TEXT NOT NULL,
            precio REAL NOT NULL,
            ubicacion TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'Disponible',
            socio_id INTEGER,
            FOREIGN KEY (socio_id) REFERENCES socios (id)
        )
    """)

    # Socio inicial si no existe
    cursor.execute("SELECT COUNT(*) FROM socios")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO socios (nombre, email, telefono, rol) VALUES (?, ?, ?, ?)",
            ("Agente Inicial CIM", "agente@cimia.com", "+54 9 376 4000000", "Administrador")
        )

    # Propiedades iniciales demo (solo si la tabla está totalmente vacía)
    cursor.execute("SELECT COUNT(*) FROM propiedades")
    if cursor.fetchone()[0] == 0:
        propiedades_demo = [
            ("Casa Quinta Oberá", "Casa", 110000000, "Oberá, Misiones", "Disponible", 1),
            ("Local Comercial Microcentro", "Local", 95000000, "Posadas, Misiones", "Vendido", 1),
            ("Terreno Zona Residencial", "Terreno", 45000000, "Garupá, Misiones", "Disponible", 1),
            ("Departamento 2 Dormitorios", "Departamento", 80000000, "Posadas, Misiones", "Reservado", 1),
            ("Oficina Corporativa Center", "Oficina", 65000000, "Posadas, Misiones", "Disponible", 1),
        ]
        cursor.executemany("""
            INSERT INTO propiedades (titulo, tipo, precio, ubicacion, estado, socio_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, propiedades_demo)

    conn.commit()
    conn.close()

init_db()

# -------------------------------------------------------------------
# MODELOS PYDANTIC
# -------------------------------------------------------------------
class SocioCreate(BaseModel):
    nombre: str
    email: str
    telefono: Optional[str] = ""
    rol: Optional[str] = "Agente"

class PropiedadCreate(BaseModel):
    titulo: str
    tipo: str
    precio: float
    ubicacion: str
    estado: Optional[str] = "Disponible"
    socio_id: Optional[int] = 1

class EstadoUpdate(BaseModel):
    estado: str

# -------------------------------------------------------------------
# ENDPOINT DE AUTENTICACIÓN / LOGIN
# -------------------------------------------------------------------
@app.post("/auth/login")
def login(username: str = Form(...), password: str = Form(...)):
    # Validación simple para prueba / demostración
    # Puedes sustituirlo por una consulta a la DB para verificar hash de contraseña
    if username and password:
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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, email, telefono, rol FROM socios ORDER BY id DESC")
    socios = [
        {"id": row[0], "nombre": row[1], "email": row[2], "telefono": row[3], "rol": row[4]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return socios

@app.post("/socios", status_code=201)
def crear_socio(socio: SocioCreate):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO socios (nombre, email, telefono, rol) VALUES (?, ?, ?, ?)",
            (socio.nombre, socio.email, socio.telefono, socio.rol)
        )
        conn.commit()
        socio_id = cursor.lastrowid
        conn.close()
        return {"id": socio_id, "mensaje": "Socio registrado con éxito"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="El email ya está registrado")

# -------------------------------------------------------------------
# ENDPOINTS DE PROPIEDADES (ADMINISTRACIÓN)
# -------------------------------------------------------------------
@app.get("/propiedades")
def obtener_propiedades():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.titulo, p.tipo, p.precio, p.ubicacion, p.estado, p.socio_id, s.nombre
        FROM propiedades p
        LEFT JOIN socios s ON p.socio_id = s.id
        ORDER BY p.id DESC
    """)
    propiedades = [
        {
            "id": row[0],
            "titulo": row[1],
            "tipo": row[2],
            "precio": row[3],
            "ubicacion": row[4],
            "estado": row[5],
            "socio_id": row[6],
            "socio_nombre": row[7] if row[7] else "Sin Agente Asignado"
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return propiedades

@app.post("/propiedades", status_code=201)
def crear_propiedad(propiedad: PropiedadCreate):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO propiedades (titulo, tipo, precio, ubicacion, estado, socio_id) VALUES (?, ?, ?, ?, ?, ?)",
        (propiedad.titulo, propiedad.tipo, propiedad.precio, propiedad.ubicacion, propiedad.estado, propiedad.socio_id)
    )
    conn.commit()
    prop_id = cursor.lastrowid
    conn.close()
    return {"id": prop_id, "mensaje": "Propiedad agregada correctamente"}

@app.patch("/propiedades/{id}/estado")
def actualizar_estado_propiedad(id: int, payload: EstadoUpdate):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE propiedades SET estado = ? WHERE id = ?", (payload.estado, id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    
    return {"mensaje": f"Estado actualizado a {payload.estado}"}

@app.delete("/propiedades/{id}")
def eliminar_propiedad(id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM propiedades WHERE id = ?", (id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    
    return {"mensaje": "Propiedad eliminada correctamente"}

# -------------------------------------------------------------------
# ENDPOINT DE ANALÍTICAS Y DASHBOARD
# -------------------------------------------------------------------
@app.get("/analiticas/resumen")
def obtener_resumen_analiticas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Total de propiedades
    cursor.execute("SELECT COUNT(*) FROM propiedades")
    propiedades_totales = cursor.fetchone()[0]

    # Propiedades estrictamente Disponibles
    cursor.execute("SELECT COUNT(*) FROM propiedades WHERE estado = 'Disponible'")
    propiedades_disponibles = cursor.fetchone()[0]

    # Usuarios/Socios registrados
    cursor.execute("SELECT COUNT(*) FROM socios")
    usuarios_registrados = cursor.fetchone()[0]

    # Valor total e indicativos
    cursor.execute("SELECT COALESCE(SUM(precio), 0), COALESCE(AVG(precio), 0) FROM propiedades")
    total_cartera, precio_promedio = cursor.fetchone()

    # Estimación comisión / MRR Proyectado (1.5% comisión sobre el valor total)
    mrr_proyectado = total_cartera * 0.015

    # Tasa de Disponibilidad (%)
    tasa_disponibilidad = (
        round((propiedades_disponibles / propiedades_totales) * 100, 1)
        if propiedades_totales > 0
        else 0
    )

    # Distribución por Tipo
    cursor.execute("SELECT tipo, COUNT(*) FROM propiedades GROUP BY tipo")
    distribucion_tipos = [
        {"tipo": row[0], "cantidad": row[1]}
        for row in cursor.fetchall()
    ]

    conn.close()

    return {
        "mrr_proyectado": round(mrr_proyectado, 2),
        "propiedades_totales": propiedades_totales,
        "propiedades_disponibles": propiedades_disponibles,
        "usuarios_registrados": usuarios_registrados,
        "precio_promedio": round(precio_promedio, 2),
        "tasa_disponibilidad": tasa_disponibilidad,
        "distribucion_tipos": distribucion_tipos
    }

# -------------------------------------------------------------------
# ENDPOINT PÚBLICO (Solo propiedades Disponibles para el cliente)
# -------------------------------------------------------------------
@app.get("/publico/propiedades")
def obtener_propiedades_publicas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.titulo, p.tipo, p.precio, p.ubicacion, s.nombre, s.telefono, s.email
        FROM propiedades p
        LEFT JOIN socios s ON p.socio_id = s.id
        WHERE p.estado = 'Disponible'
        ORDER BY p.id DESC
    """)
    propiedades = [
        {
            "id": row[0],
            "titulo": row[1],
            "tipo": row[2],
            "precio": row[3],
            "ubicacion": row[4],
            "agente_nombre": row[5] if row[5] else "Inmobiliaria CIM",
            "agente_telefono": row[6] if row[6] else "",
            "agente_email": row[7] if row[7] else ""
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return propiedades