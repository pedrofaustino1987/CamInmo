SELECT * FROM socios_inmobiliarios;
SELECT s.id_socio, s.nombre_comercial, p.nombre AS plan_actual, p.limite_propiedades
FROM socios_inmobiliarios s
JOIN planes_saas p ON s.id_plan_actual = p.id_plan
LIMIT 10;
INSERT INTO propiedades (id_socio, titulo, descripcion, tipo_operacion, tipo_inmueble, precio, moneda, localidad)
VALUES (1, 'Departamento de 2 Dormitorios Centro', 'Hermoso depto en duplex, cochera incluida.', 'VENTA', 'DEPARTAMENTO', 65000.00, 'USD', 'Posadas');
SELECT * FROM propiedades WHERE id_socio = 1;
INSERT INTO transacciones_comisiones 
(id_propiedad, id_socio, monto_operacion, porcentaje_comision_corredor, monto_comision_total, fee_plataforma_cim, estado_pago)
VALUES 
(1, 1, 65000.00, 5.0, 3250.00, 325.00, 'COMPLETADO');
CREATE TRIGGER antes_insertar_propiedad_limite
BEFORE INSERT ON propiedades
BEGIN
    SELECT
        CASE
            -- Verificamos si el plan tiene un límite mayor o igual a 0 (los planes ilimitados usan -1)
            WHEN (SELECT limite_propiedades FROM planes_saas WHERE id_plan = (SELECT id_plan_actual FROM socios_inmobiliarios WHERE id_socio = NEW.id_socio)) >= 0
                 AND
                 -- Contamos las propiedades actualmente activas de esa inmobiliaria
                 (SELECT COUNT(*) FROM propiedades WHERE id_socio = NEW.id_socio AND estado = 'DISPONIBLE') >= 
                 (SELECT limite_propiedades FROM planes_saas WHERE id_plan = (SELECT id_plan_actual FROM socios_inmobiliarios WHERE id_socio = NEW.id_socio))
            THEN 
                 -- Si excede el límite, aborta la transacción y devuelve un error explícito a la aplicación
                 RAISE(ABORT, 'Error Operativo: La inmobiliaria ha alcanzado el límite máximo de propiedades disponibles permitidas por su plan SaaS actual.')
        END;
END;
CREATE TRIGGER validar_integridad_comisiones
BEFORE INSERT ON transacciones_comisiones
BEGIN
    SELECT
        CASE
            -- Asegurar que el monto registrado en la plataforma coincida exactamente con las matemáticas del negocio
            WHEN ABS(NEW.monto_comision_total - (NEW.monto_operacion * (NEW.porcentaje_comision_corredor / 100.0))) > 0.01
            THEN RAISE(ABORT, 'Error de Integridad Financiera: El monto_comision_total no coincide con el porcentaje matemático de la operación.')
            
            -- Asegurar que el fee de CIM IA esté correctamente liquidado (10% de la comisión)
            WHEN ABS(NEW.fee_plataforma_cim - (NEW.monto_comision_total * 0.10)) > 0.01
            THEN RAISE(ABORT, 'Error de Liquidación: El fee de la plataforma CIM IA debe corresponder exactamente al 10% de la comisión total.')
        END;
END;
DROP TRIGGER IF EXISTS antes_insertar_calcular_comision;
DROP TRIGGER IF EXISTS validar_integridad_comisiones;

CREATE TRIGGER validar_integridad_comisiones
BEFORE INSERT ON transacciones_comisiones
BEGIN
    SELECT
        CASE
            -- 1. Validar que el porcentaje de comisión esté en el rango correcto
            WHEN NEW.porcentaje_comision_corredor < 0 OR NEW.porcentaje_comision_corredor > 100
            THEN RAISE(ABORT, 'Error de Validacion: El porcentaje de comision del corredor debe estar entre 0 y 100.')
            
            -- 2. Validar que el monto de la comisión coincida con la matemática del negocio
            WHEN ABS(NEW.monto_comision_total - (NEW.monto_operacion * (NEW.porcentaje_comision_corredor / 100.0))) > 0.01
            THEN RAISE(ABORT, 'Error de Integridad Financiera: El monto_comision_total no coincide con el porcentaje real.')
            
            -- 3. Validar que el fee de la plataforma CIM IA sea exactamente el 10% de la comisión del corredor
            WHEN ABS(NEW.fee_plataforma_cim - (NEW.monto_comision_total * 0.10)) > 0.01
            THEN RAISE(ABORT, 'Error de Liquidacion: El fee de la plataforma CIM IA debe corresponder al 10% de la comision total.')
        END;
END;

DROP TRIGGER IF EXISTS calcular_comisiones_automatico;

CREATE TRIGGER calcular_comisiones_automatico
AFTER INSERT ON transacciones_comisiones
BEGIN
    UPDATE transacciones_comisiones
    SET 
        -- 1. Calcula la comisión total del corredor (Monto de operación * Porcentaje)
        monto_comision_total = NEW.monto_operacion * (NEW.porcentaje_comision_corredor / 100.0),
        
        -- 2. Calcula el fee del 10% para la plataforma CIM IA sobre esa comisión
        fee_plataforma_cim = (NEW.monto_operacion * (NEW.porcentaje_comision_corredor / 100.0)) * 0.10
    WHERE id_transaccion = NEW.id_transaccion;
END;
-- Eliminar definitivamente el trigger de validación que está bloqueando el cero
DROP TRIGGER IF EXISTS validar_integridad_comisiones;
DROP TRIGGER IF EXISTS calcular_comisiones_automatico;

-- Crear el trigger definitivo de automatización pura
CREATE TRIGGER calcular_comisiones_automatico
AFTER INSERT ON transacciones_comisiones
BEGIN
    UPDATE transacciones_comisiones
    SET 
        monto_comision_total = NEW.monto_operacion * (NEW.porcentaje_comision_corredor / 100.0),
        fee_plataforma_cim = (NEW.monto_operacion * (NEW.porcentaje_comision_corredor / 100.0)) * 0.10
    WHERE id_transaccion = NEW.id_transaccion;
END;
-- Asegurar que exista la propiedad de prueba vinculada al socio
INSERT OR IGNORE INTO propiedades (id_propiedad, id_socio, titulo, tipo_operacion, tipo_inmueble, precio, localidad)
VALUES (1, 1, 'Propiedad de Prueba', 'VENTA', 'CASA', 150000.00, 'Posadas');

-- Insertar la transacción (ahora sí aceptará el 0.0 porque el validador viejo fue removido)
INSERT INTO transacciones_comisiones 
(id_propiedad, id_socio, monto_operacion, porcentaje_comision_corredor, monto_comision_total, fee_plataforma_cim, estado_pago)
VALUES (1, 1, 150000.00, 4.0, 0.0, 0.0, 'COMPLETADO');

-- Comprobar que el sistema calculó los valores de manera interna
SELECT monto_operacion, porcentaje_comision_corredor, monto_comision_total, fee_plataforma_cim 
FROM transacciones_comisiones 
ORDER BY id_transaccion DESC LIMIT 1;
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
-- Esto va a Fallar adrede debido al Trigger de Privacidad
INSERT INTO usuarios_empleados (id_socio, nombre_completo, email, password_hash, rol, acepto_terminos)
VALUES (1, 'Juan Pérez', 'juan.perez@araucaria.com', 'hash_seguro_123', 'AGENTE', 0);