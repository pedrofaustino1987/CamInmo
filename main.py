import sqlite3
import os
import shutil
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List

DB_NAME = "CamInmo.db"
UPLOAD_DIR = "uploads"
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -------------------------------------------------------------------
# SCRIPT SQL EXACTO DE ESTRUCTURA Y DATOS INICIALES
# -------------------------------------------------------------------
INIT_SQL_SCRIPT = """
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "planes_saas" (
	"id_plan"	INTEGER,
	"nombre"	TEXT NOT NULL UNIQUE,
	"precio_mensual"	REAL NOT NULL,
	"limite_propiedades"	INTEGER NOT NULL,
	"permite_ia"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id_plan" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "socios" (
	"id"	INTEGER,
	"nombre"	TEXT NOT NULL,
	"email"	TEXT,
	"telefono"	TEXT,
	"estado"	TEXT DEFAULT 'Activo',
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "propiedades" (
	"id"	INTEGER,
	"titulo"	TEXT NOT NULL,
	"tipo"	TEXT NOT NULL,
	"precio"	REAL NOT NULL,
	"estado"	TEXT DEFAULT 'Disponible',
	"ubicacion"	TEXT,
	"socio_id"	INTEGER DEFAULT 1,
	"imagen_url"	TEXT,
	"moneda"	TEXT DEFAULT 'USD',
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("socio_id") REFERENCES "socios_inmobiliarios"("id_socio")
);
CREATE TABLE IF NOT EXISTS "socios_inmobiliarios" (
	"id_socio"	INTEGER,
	"nombre_comercial"	TEXT NOT NULL UNIQUE,
	"cuit"	TEXT UNIQUE,
	"matricula_corredor"	TEXT,
	"estado_camara"	TEXT DEFAULT 'ACTIVO',
	"id_plan_actual"	INTEGER NOT NULL,
	"fecha_registro"	TEXT DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id_socio" AUTOINCREMENT),
	FOREIGN KEY("id_plan_actual") REFERENCES "planes_saas"("id_plan")
);
CREATE TABLE IF NOT EXISTS "transacciones_comisiones" (
	"id_transaccion"	INTEGER,
	"id_propiedad"	INTEGER NOT NULL,
	"id_socio"	INTEGER NOT NULL,
	"monto_operacion"	REAL NOT NULL,
	"porcentaje_comision_corredor"	REAL NOT NULL,
	"monto_comision_total"	REAL NOT NULL,
	"fee_plataforma_cim"	REAL NOT NULL,
	"estado_pago"	TEXT NOT NULL DEFAULT 'PENDIENTE',
	"fecha_transaccion"	TEXT DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id_transaccion" AUTOINCREMENT),
	FOREIGN KEY("id_propiedad") REFERENCES "propiedades"("id"),
	FOREIGN KEY("id_socio") REFERENCES "socios_inmobiliarios"("id_socio")
);
CREATE TABLE IF NOT EXISTS "usuarios_empleados" (
	"id_usuario"	INTEGER,
	"id_socio"	INTEGER NOT NULL,
	"nombre_completo"	TEXT NOT NULL,
	"email"	TEXT NOT NULL UNIQUE,
	"password_hash"	TEXT NOT NULL,
	"rol"	TEXT NOT NULL DEFAULT 'AGENTE',
	"acepto_terminos"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id_usuario" AUTOINCREMENT),
	FOREIGN KEY("id_socio") REFERENCES "socios_inmobiliarios"("id_socio") ON DELETE CASCADE
);

-- INSERCIÓN DE DATOS INICIALES (Sólo si las tablas están vacías)
INSERT OR IGNORE INTO "planes_saas" VALUES (1,'Básico',30000.0,50,0);
INSERT OR IGNORE INTO "planes_saas" VALUES (2,'Profesional',70000.0,-1,1);
INSERT OR IGNORE INTO "planes_saas" VALUES (3,'Enterprise',0.0,-1,1);

INSERT OR IGNORE INTO "socios" VALUES (1,'Agente Inicial CIM','agente@cimia.com','+54 376 4000000','Activo');

INSERT OR IGNORE INTO "socios_inmobiliarios" VALUES 
(1,'ARAUCARIA PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(2,'ARQUIN',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(3,'AZUL PROPIEDADES (JUAN GONZALEZ)',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(4,'BERGOTTINI BIENES RAICES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(5,'CARLES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(6,'CARRAFA FLORES INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(7,'CELMAN PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(8,'CHALANCZUK PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(9,'CHIOFALO & NADICH',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(10,'CORA CAMPOS',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(11,'DAVIÑA PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(12,'DEL OESTE INMUEBLES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(13,'DELLAPIERRE',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(14,'FERNANDEZ INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(15,'FERREIRA INMUEBLES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(16,'FIDANZA INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(17,'FORESTAL LA RAMA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(18,'FUENTES PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(19,'G30 ESTUDIO INMOBILIARIO',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(20,'GARUPA PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(21,'GAUTO FECHNER INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(22,'GIMENEZ & GIMENES INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(23,'GRACIELA ARCE',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(24,'GUAYRA PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(25,'GUTLEBER PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(26,'GYS PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(27,'HITO INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(28,'HOSLVAK PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(29,'IGUAZU INMUEBLES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(30,'INGENIERO RESEK',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(31,'INMOBILIARIA SITIOS',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(32,'INNOVA INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(33,'IVO GÔTZ',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(34,'JANIEL PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(35,'KAMADA INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(36,'KUNZ PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(37,'LA CAPITAL PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(38,'LATINA S.A.',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(39,'LILIANA DURAN PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(40,'LOSAVIO & FULKET PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(41,'LOSAVIO DANIEL',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(42,'MANECO PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(43,'MARCELO MARINI INVERSIONES INMOBILIARIAS',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(44,'MARIA BOWER',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(45,'MELINA ROMERO INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(46,'MERCEDES BONETTI INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(47,'MIRTA MARCON INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(48,'MISIONES INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(49,'MONICA FOGELER INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(50,'MONSU PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(51,'MyM PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(52,'NEXOS INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(53,'NIELLA PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(54,'ORTIZ INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(55,'P.O.E.A.',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(56,'PLATINIUM INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(57,'RAICES INMOBILIARIA (MACIEL, ELDORADO)',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(58,'RAICES INMOBILIARIA (MARCO W.)',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(59,'RAUL CARRIZO INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(60,'RIMA PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(61,'ROBLES PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(62,'RYS PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(63,'SAMUDIO HALLEY AIDA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(64,'SEDKO PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(65,'SOLARI INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(66,'SONIA PEREYRA INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(67,'SOSA PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(68,'TEIJEIRO PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(69,'ULISES VALLARO INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(70,'V PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(71,'VANINA PAULUK INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(72,'VIBA PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(73,'ZAPANI PROPIEDADES',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(74,'ZUNY FERNANDEZ INMOBILIARIA',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40'),
(75,'SINGULAR',NULL,NULL,'ACTIVO',1,'2026-07-19 17:12:40');

INSERT OR IGNORE INTO "propiedades" VALUES 
(1,'Casa de Campo en Posadas','Casa',120000000.0,'Vendido','Posadas, Misiones',1,NULL,'USD'),
(2,'Departamento Céntrico 2D','Departamento',85000000.0,'Vendido','Posadas, Misiones',1,NULL,'USD'),
(3,'Terreno Zona Garupá','Terreno',35000000.0,'Vendido','Garupá, Misiones',1,NULL,'USD'),
(4,'Local Comercial Microcentro','Local',95000000.0,'Vendido','Posadas, Misiones',1,NULL,'USD'),
(5,'Casa Quinta Oberá','Casa',110000000.0,'Vendido','Oberá, Misiones',1,NULL,'USD');

INSERT OR IGNORE INTO "transacciones_comisiones" VALUES 
(1,1,1,65000.0,5.0,3250.0,325.0,'COMPLETADO','2026-07-19 17:33:08'),
(2,1,1,150000.0,4.0,6000.0,600.0,'COMPLETADO','2026-07-19 18:01:24');

INSERT OR IGNORE INTO "usuarios_empleados" VALUES 
(1,1,'Juan Pérez','juan@posadascentro.com','hash_pass_123','ADMIN',1),
(2,1,'María Gómez','maria@posadascentro.com','hash_pass_456','AGENTE',1),
(3,2,'Carlos Rodríguez','carlos@garupaprop.com','hash_pass_789','ADMIN',1),
(4,3,'Ana Martínez','ana@oberabr.com','hash_pass_321','AGENTE',1);

-- TRIGGERS
DROP TRIGGER IF EXISTS calcular_comisiones_automatico;
CREATE TRIGGER calcular_comisiones_automatico
AFTER INSERT ON transacciones_comisiones
BEGIN
    UPDATE transacciones_comisiones
    SET 
        monto_comision_total = NEW.monto_operacion * (NEW.porcentaje_comision_corredor / 100.0),
        fee_plataforma_cim = (NEW.monto_operacion * (NEW.porcentaje_comision_corredor / 100.0)) * 0.10
    WHERE id_transaccion = NEW.id_transaccion;
END;

DROP TRIGGER IF EXISTS requerir_consentimiento_ley25326;
CREATE TRIGGER requerir_consentimiento_ley25326
BEFORE INSERT ON usuarios_empleados
BEGIN
    SELECT
        CASE
            WHEN NEW.acepto_terminos != 1
            THEN RAISE(ABORT, 'Error Legal: No se puede registrar al usuario sin el consentimiento explícito de términos y condiciones (Ley N.º 25.326).')
        END;
END;

COMMIT;
"""

# -------------------------------------------------------------------
# HELPER DE CONEXIÓN Y CREACIÓN INICIAL
# -------------------------------------------------------------------
@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()

def inicializar_bd():
    """Ejecuta el script SQL completo para asegurar la estructura exacta."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.executescript(INIT_SQL_SCRIPT)
        conn.close()
        print(f"✅ Base de datos '{DB_NAME}' creada y sincronizada exitosamente con todas sus tablas, datos y triggers.")
    except Exception as e:
        print(f"⚠️ Nota de Inicialización BD: {e}")

# Se ejecuta al cargar el archivo
inicializar_bd()

# -------------------------------------------------------------------
# INICIALIZACIÓN DE FASTAPI
# -------------------------------------------------------------------
app = FastAPI(title="CamInmo - Sistema Inmobiliario Backend")

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# MODELOS PYDANTIC
# -------------------------------------------------------------------
class PropiedadCreate(BaseModel):
    titulo: Optional[str] = "Propiedad Sin Título"
    tipo: Optional[str] = "Casa"
    precio: Optional[float] = 0.0
    moneda: Optional[str] = "USD"
    ubicacion: Optional[str] = "Sin ubicación"
    estado: Optional[str] = "Disponible"
    socio_id: Optional[int] = 1
    socioId: Optional[int] = None

class PropiedadUpdate(BaseModel):
    titulo: str
    tipo: str
    precio: float
    moneda: Optional[str] = "USD"
    ubicacion: str
    estado: Optional[str] = "Disponible"
    socio_id: Optional[int] = 1

class EstadoUpdate(BaseModel):
    estado: str

# -------------------------------------------------------------------
# ENDPOINTS ADAPTADOS A LA NUEVA ESTRUCTURA
# -------------------------------------------------------------------
@app.get("/socios")
def obtener_socios():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT s.id_socio, s.nombre_comercial, u.email, u.nombre_completo, u.rol
            FROM socios_inmobiliarios s
            LEFT JOIN usuarios_empleados u ON s.id_socio = u.id_socio
            GROUP BY s.id_socio
            ORDER BY s.id_socio DESC
        """).fetchall()

    return [
        {
            "id": row[0],
            "nombre": row[1],
            "email": row[2] if row[2] else "contacto@inmobiliaria.com",
            "telefono": "+54 9 376 4000000",
            "rol": row[4] if row[4] else "AGENTE"
        }
        for row in rows
    ]

@app.get("/propiedades")
def obtener_propiedades():
    try:
        with get_db() as conn:
            rows = conn.execute("""
                SELECT p.id, p.titulo, p.tipo, p.precio, p.ubicacion, p.estado, p.socio_id, s.nombre_comercial, p.imagen_url, p.moneda
                FROM propiedades p
                LEFT JOIN socios_inmobiliarios s ON p.socio_id = s.id_socio
                ORDER BY p.id DESC
            """).fetchall()

        return [
            {
                "id": row[0],
                "titulo": row[1],
                "tipo": row[2],
                "precio": row[3],
                "ubicacion": row[4],
                "estado": row[5],
                "socio_id": row[6],
                "socio_nombre": row[7] if row[7] else "Agente CIM",
                "socio_email": "agente@cimia.com",
                "imagen_url": row[8],
                "moneda": row[9] if row[9] else "USD"
            }
            for row in rows
        ]
    except Exception as e:
        print(f"❌ Error al obtener propiedades: {e}")
        return []

@app.post("/propiedades", status_code=201)
def crear_propiedad(propiedad: PropiedadCreate):
    try:
        socio_final = propiedad.socio_id or propiedad.socioId or 1
        estado_db = propiedad.estado or "Disponible"
        moneda_db = propiedad.moneda or "USD"
        
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO propiedades (titulo, tipo, precio, estado, ubicacion, socio_id, moneda)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (propiedad.titulo, propiedad.tipo, propiedad.precio, estado_db, propiedad.ubicacion, socio_final, moneda_db))
            conn.commit()
            prop_id = cursor.lastrowid

        return {"id": prop_id, "mensaje": "Propiedad creada con éxito"}
    except Exception as e:
        print(f"❌ Error al crear propiedad: {e}")
        raise HTTPException(status_code=400, detail=f"Error en BD: {str(e)}")

@app.post("/propiedades/{id}/imagen")
async def subir_imagen_propiedad(id: int, file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo enviado debe ser una imagen.")

    extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"propiedad_{id}.{extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_url = f"{BASE_URL}/uploads/{filename}"

    with get_db() as conn:
        cursor = conn.execute("UPDATE propiedades SET imagen_url = ? WHERE id = ?", (image_url, id))
        conn.commit()
        affected = cursor.rowcount

    if affected == 0:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    return {"status": "ok", "imagen_url": image_url}

@app.delete("/propiedades/{id}")
def eliminar_propiedad(id: int):
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM propiedades WHERE id = ?", (id,))
        conn.commit()
        affected = cursor.rowcount
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    
    return {"mensaje": "Propiedad eliminada correctamente"}