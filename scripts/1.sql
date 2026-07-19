-- Habilitar el soporte de claves foráneas en SQLite
PRAGMA foreign_keys = ON;

-- 1. TABLA: Planes de Suscripción SaaS
CREATE TABLE planes_saas (
    id_plan INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,          -- 'Básico', 'Profesional', 'Enterprise'
    precio_mensual REAL NOT NULL,         -- 30000.00, 70000.00, etc.
    limite_propiedades INTEGER NOT NULL,  -- 50 para básico, -1 para ilimitado
    permite_ia INTEGER NOT NULL DEFAULT 0 -- 0 = No, 1 = Sí (Control de madurez de IA)
);

-- 2. TABLA: Socios de la Cámara Inmobiliaria de Misiones (Inmobiliarias)
CREATE TABLE socios_inmobiliarios (
    id_socio INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_comercial TEXT NOT NULL UNIQUE, 
    cuit TEXT UNIQUE,                     -- Para validación legal y tributaria
    matricula_corredor TEXT,              -- Obligatorio para operar legalmente
    estado_camara TEXT DEFAULT 'ACTIVO',  -- Estado dentro de la CIM
    id_plan_actual INTEGER NOT NULL,
    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_plan_actual) REFERENCES planes_saas(id_plan)
);

-- 3. TABLA: Usuarios del Sistema (Para el personal de las inmobiliarias)
-- Responde a la Ley 25.326: Manejo de accesos y consentimiento
CREATE TABLE usuarios_empleados (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    id_socio INTEGER NOT NULL,
    nombre_completo TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,          -- Las contraseñas SIEMPRE encriptadas
    rol TEXT NOT NULL DEFAULT 'AGENTE',    -- 'ADMIN', 'AGENTE'
    acepto_terminos INTEGER NOT NULL DEFAULT 0, -- 1 = Dio consentimiento de datos (Ley 25.326)
    FOREIGN KEY (id_socio) REFERENCES socios_inmobiliarios(id_socio) ON DELETE CASCADE
);

-- 4. TABLA: Propiedades
CREATE TABLE propiedades (
    id_propiedad INTEGER PRIMARY KEY AUTOINCREMENT,
    id_socio INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    tipo_operacion TEXT NOT NULL,         -- 'VENTA', 'ALQUILER'
    tipo_inmueble TEXT NOT NULL,          -- 'CASA', 'DEPARTAMENTO', 'TERRENO'
    precio REAL NOT NULL,
    moneda TEXT NOT NULL DEFAULT 'USD',   -- 'USD', 'ARS'
    localidad TEXT NOT NULL,              -- 'Posadas', 'Garupá', 'Eldorado', etc.
    estado TEXT NOT NULL DEFAULT 'DISPONIBLE', -- 'DISPONIBLE', 'RESERVADO', 'VENDIDO'
    fecha_publicacion TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_socio) REFERENCES socios_inmobiliarios(id_socio) ON DELETE CASCADE
);

-- 5. TABLA: Sistema de Pagos Integrado e Incentivos
-- Registra el cobro de comisiones y el fee tecnológico de CIM IA
CREATE TABLE transacciones_comisiones (
    id_transaccion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_propiedad INTEGER NOT NULL,
    id_socio INTEGER NOT NULL,
    monto_operacion REAL NOT NULL,
    porcentaje_comision_corredor REAL NOT NULL, -- Ej: 5.0 (significa 5%)
    monto_comision_total REAL NOT NULL,         -- El 5% del valor total
    fee_plataforma_cim REAL NOT NULL,           -- El cargo tecnológico cobrado por CIM IA
    estado_pago TEXT NOT NULL DEFAULT 'PENDIENTE', -- 'PENDIENTE', 'COMPLETADO', 'FALLIDO'
    fecha_transaccion TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_propiedad) REFERENCES propiedades(id_propiedad),
    FOREIGN KEY (id_socio) REFERENCES socios_inmobiliarios(id_socio)
);