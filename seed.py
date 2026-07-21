import sqlite3
from database import get_db_connection

def cargar_datos_prueba():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Insertar Planes SaaS
        cursor.execute("""
            INSERT OR IGNORE INTO planes_saas (id_plan, nombre, precio_mensual, limite_propiedades, permite_ia)
            VALUES 
                (1, 'Básico', 35000.00, 50, 0),
                (2, 'Profesional', 75000.00, 200, 1),
                (3, 'Enterprise', 15000.00, -1, 1);
        """)

        # 2. Insertar Socios Inmobiliarios de Misiones
        cursor.execute("""
            INSERT OR IGNORE INTO socios_inmobiliarios (id_socio, nombre_comercial, cuit, matricula_corredor, estado_camara, id_plan_actual)
            VALUES 
                (1, 'Inmobiliaria Posadas Centro', '30-12345678-9', 'MAT-045', 'ACTIVO', 2),
                (2, 'Garupá Propiedades', '30-87654321-4', 'MAT-112', 'ACTIVO', 1),
                (3, 'Oberá Bienes Raíces', '30-55556666-1', 'MAT-089', 'ACTIVO', 2);
        """)

        # 3. Insertar Usuarios
        cursor.execute("""
            INSERT OR IGNORE INTO usuarios_empleados (id_usuario, id_socio, nombre_completo, email, password_hash, rol, acepto_terminos)
            VALUES 
                (1, 1, 'Juan Pérez', 'juan@posadascentro.com', 'hash_pass_123', 'ADMIN', 1),
                (2, 1, 'María Gómez', 'maria@posadascentro.com', 'hash_pass_456', 'AGENTE', 1),
                (3, 2, 'Carlos Rodríguez', 'carlos@garupaprop.com', 'hash_pass_789', 'ADMIN', 1),
                (4, 3, 'Ana Martínez', 'ana@oberabr.com', 'hash_pass_321', 'AGENTE', 1);
        """)

        # 4. Insertar Propiedades
        cursor.execute("""
            INSERT OR IGNORE INTO propiedades (id_propiedad, id_socio, titulo, descripcion, tipo_operacion, tipo_inmueble, precio, moneda, localidad, estado)
            VALUES 
                (1, 1, 'Departamento 2 Dormitorios - Costanera', 'Vista al río Paraná', 'VENTA', 'DEPARTAMENTO', 85000.00, 'USD', 'Posadas', 'DISPONIBLE'),
                (2, 1, 'Casa Quinta con Pileta', 'Amplia casa en zona residencial', 'VENTA', 'CASA', 120000.00, 'USD', 'Posadas', 'DISPONIBLE'),
                (3, 2, 'Terreno Comercial Garupá', 'Excelente ubicación sobre ruta', 'VENTA', 'TERRENO', 25000.00, 'USD', 'Garupá', 'DISPONIBLE'),
                (4, 3, 'Casa Centro Oberá', '3 dormitorios, garage', 'ALQUILER', 'CASA', 350000.00, 'ARS', 'Oberá', 'DISPONIBLE');
        """)

        conn.commit()
        print("¡Datos de prueba cargados con éxito en la Base de Datos!")

if __name__ == "__main__":
    cargar_datos_prueba()