from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
from database import get_db_connection

app = FastAPI(
    title="CIM IA API",
    description="Backend modular para el MVP de la plataforma inmobiliaria de Misiones.",
    version="1.0.0"
)

# --- MODELOS DE ENTRADA (Validación Pydantic) ---
# Responde a la Ley 25.326: El backend exige que el consentimiento sea explícito (acepto_terminos = True)
class RegistroUsuario(BaseModel):
    id_socio: int
    nombre_completo: str
    email: EmailStr
    password_hash: str
    rol: str = "AGENTE"
    acepto_terminos: bool

# --- RUTAS / ENDPOINTS ---

@app.get("/", tags=["General"])
def inicio():
    return {"mensaje": "Bienvenido a la API de CIM IA - Sistema Operativo Comercial"}


@app.get("/analiticas/saas", tags=["Panel de Control"])
def obtener_facturacion_saas():
    """
    Ejecuta la consulta analítica para obtener el Ingreso Recurrente Mensual (MRR)
    basado en las suscripciones activas de los socios de la cámara.
    """
    query = """
    SELECT 
        p.nombre AS Plan,
        p.precio_mensual AS Costo_Plan_ARS,
        COUNT(s.id_socio) AS Cantidad_Inmobiliarias,
        (COUNT(s.id_socio) * p.precio_mensual) AS Total_Mensual_Estimado_ARS
    FROM socios_inmobiliarios s
    JOIN planes_saas p ON s.id_plan_actual = p.id_plan
    GROUP BY p.id_plan;
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        filas = cursor.fetchall()
        
        # Convertimos las filas de SQLite en una lista de diccionarios JSON
        resultado = [dict(fila) for fila in filas]
        return resultado


@app.post("/usuarios/registrar", tags=["Seguridad y Ley 25.326"])
def registrar_usuario(usuario: RegistroUsuario):
    """
    Endpoint para dar de alta empleados inmobiliarios.
    Si acepto_terminos es False, Pydantic o el Trigger de SQLite bloquearán la acción.
    """
    # Validación extra en Backend antes de tocar la BD
    if not usuario.acepto_terminos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error Legal: Debe aceptar los términos y condiciones para almacenar datos personales."
        )
        
    query = """
    INSERT INTO usuarios_empleados (id_socio, nombre_completo, email, password_hash, rol, acepto_terminos)
    VALUES (?, ?, ?, ?, ?, ?);
    """
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, (
                usuario.id_socio,
                usuario.nombre_completo,
                usuario.email,
                usuario.password_hash,
                usuario.rol,
                1 if usuario.acepto_terminos else 0
            ))
            conn.commit()
            return {"status": "Éxito", "mensaje": "Usuario registrado en cumplimiento con la Ley 25.326."}
        except sqlite3.IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error de Consistencia en Base de Datos: {str(e)}"
            )