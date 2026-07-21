import sqlite3
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="CIM IA - API Inmobiliaria",
    description="Backend para panel central e infraestructura analítica",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_NAME = "CamInmo.db"

# Esquema Pydantic para validar la entrada de nuevas propiedades
class PropiedadCrear(BaseModel):
    titulo: str
    tipo: str
    precio: float
    estado: str = "Disponible"
    ubicacion: str

@contextmanager
def obtener_conexion():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def inicializar_tablas(conn):
    cursor = conn.cursor()
    
    # 1. Tabla de socios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS socios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT,
            telefono TEXT,
            estado TEXT DEFAULT 'Activo'
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM socios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO socios (nombre, email, telefono, estado) 
            VALUES ('Agente Inicial CIM', 'agente@cimia.com', '+54 376 4000000', 'Activo')
        """)

    # 2. Tabla de propiedades (sin DROP para preservar registros guardados)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS propiedades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            tipo TEXT NOT NULL,
            precio REAL NOT NULL,
            estado TEXT DEFAULT 'Disponible',
            ubicacion TEXT
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM propiedades")
    if cursor.fetchone()[0] == 0:
        propiedades_demo = [
            ('Casa de Campo en Posadas', 'Casa', 120000000, 'Disponible', 'Posadas, Misiones'),
            ('Departamento Céntrico 2D', 'Departamento', 85000000, 'Disponible', 'Posadas, Misiones'),
            ('Terreno Zona Garupá', 'Terreno', 35000000, 'Disponible', 'Garupá, Misiones'),
            ('Local Comercial Microcentro', 'Local', 95000000, 'Disponible', 'Posadas, Misiones'),
            ('Casa Quinta Oberá', 'Casa', 110000000, 'Reservado', 'Oberá, Misiones'),
        ]
        cursor.executemany("""
            INSERT INTO propiedades (titulo, tipo, precio, estado, ubicacion)
            VALUES (?, ?, ?, ?, ?)
        """, propiedades_demo)

    conn.commit()


@app.get("/")
def read_root():
    return {"status": "ok", "message": "API CIM IA Conectada"}


@app.get("/analiticas/resumen")
def obtener_resumen_analiticas():
    try:
        with obtener_conexion() as conn:
            inicializar_tablas(conn)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM socios")
            total_socios = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM propiedades")
            total_propiedades = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM propiedades WHERE estado = 'Disponible'")
            propiedades_disponibles = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(precio), SUM(precio) FROM propiedades")
            row_precios = cursor.fetchone()
            precio_promedio = row_precios[0] or 0
            suma_precios = row_precios[1] or 0

            mrr_proyectado = int(suma_precios * 0.015) if suma_precios > 0 else 2250000

            cursor.execute("""
                SELECT tipo, COUNT(*) as cantidad 
                FROM propiedades 
                GROUP BY tipo
            """)
            distribucion_tipos = [dict(row) for row in cursor.fetchall()]

            tasa_disponibilidad = round((propiedades_disponibles / total_propiedades * 100), 1) if total_propiedades > 0 else 0

            return {
                "mrr_proyectado": mrr_proyectado,
                "propiedades_totales": total_propiedades,
                "propiedades_disponibles": propiedades_disponibles,
                "usuarios_registrados": total_socios,
                "precio_promedio": round(precio_promedio, 2),
                "tasa_disponibilidad": tasa_disponibilidad,
                "distribucion_tipos": distribucion_tipos
            }

    except Exception as e:
        print(f"Error en /analiticas/resumen: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/propiedades")
def obtener_propiedades():
    """Ruta para listar todas las propiedades"""
    try:
        with obtener_conexion() as conn:
            inicializar_tablas(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM propiedades ORDER BY id DESC")
            return [dict(fila) for fila in cursor.fetchall()]
    except Exception as e:
        print(f"Error en GET /propiedades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/propiedades")
def crear_propiedad(propiedad: PropiedadCrear):
    """Ruta para dar de alta un nuevo inmueble"""
    try:
        with obtener_conexion() as conn:
            inicializar_tablas(conn)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO propiedades (titulo, tipo, precio, estado, ubicacion)
                VALUES (?, ?, ?, ?, ?)
            """, (propiedad.titulo, propiedad.tipo, propiedad.precio, propiedad.estado, propiedad.ubicacion))
            conn.commit()
            nuevo_id = cursor.lastrowid
            return {"status": "ok", "message": "Propiedad agregada con éxito", "id": nuevo_id}
    except Exception as e:
        print(f"Error en POST /propiedades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/socios")
def obtener_socios():
    try:
        with obtener_conexion() as conn:
            inicializar_tablas(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM socios")
            return [dict(fila) for fila in cursor.fetchall()]
    except Exception as e:
        print(f"Error en /socios: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analiticas/saas")
def obtener_analiticas_saas():
    return [
        {
            "Plan": "Básico Inmobiliario",
            "Costo_Plan_ARS": 15000,
            "Cantidad_Inmobiliarias": 12,
            "Total_Mensual_Estimado_ARS": 180000
        },
        {
            "Plan": "Pro Cámaras / Agentes",
            "Costo_Plan_ARS": 35000,
            "Cantidad_Inmobiliarias": 8,
            "Total_Mensual_Estimado_ARS": 280000
        },
        {
            "Plan": "Enterprise / Desarrolladores",
            "Costo_Plan_ARS": 75000,
            "Cantidad_Inmobiliarias": 3,
            "Total_Mensual_Estimado_ARS": 225000
        }
    ]

@app.delete("/propiedades/{propiedad_id}")
def eliminar_propiedad(propiedad_id: int):
    try:
        with obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM propiedades WHERE id = ?", (propiedad_id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Propiedad no encontrada")
                
            return {"status": "ok", "message": f"Propiedad {propiedad_id} eliminada con éxito"}
    except Exception as e:
        print(f"Error en DELETE /propiedades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class PropiedadEstadoUpdate(BaseModel):
    estado: str

@app.patch("/propiedades/{propiedad_id}/estado")
def actualizar_estado_propiedad(propiedad_id: int, datos: PropiedadEstadoUpdate):
    """Ruta para cambiar dinámicamente el estado de un inmueble (Disponible, Reservado, Vendido)"""
    try:
        with obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE propiedades 
                SET estado = ? 
                WHERE id = ?
            """, (datos.estado, propiedad_id))
            conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Propiedad no encontrada")
                
            return {"status": "ok", "message": f"Estado de propiedad {propiedad_id} actualizado a {datos.estado}"}
    except Exception as e:
        print(f"Error en PATCH /propiedades/{propiedad_id}/estado: {e}")
        raise HTTPException(status_code=500, detail=str(e))