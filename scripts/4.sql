SELECT 
    p.nombre AS Plan,
    p.precio_mensual AS Costo_Plan_ARS,
    COUNT(s.id_socio) AS Cantidad_Inmobiliarias,
    (COUNT(s.id_socio) * p.precio_mensual) AS Total_Mensual_Estimado_ARS
FROM socios_inmobiliarios s
JOIN planes_saas p ON s.id_plan_actual = p.id_plan
GROUP BY p.id_plan;
SELECT 
    COUNT(id_transaccion) AS Total_Ventas_Procesadas,
    SUM(monto_operacion) AS Volumen_Total_Movilizado_USD,
    SUM(monto_comision_total) AS Total_Comisiones_Corredores_USD,
    SUM(fee_plataforma_cim) AS Ingreso_Neto_CIM_IA_USD
FROM transacciones_comisiones
WHERE estado_pago = 'COMPLETADO';
SELECT 
    s.nombre_comercial AS Inmobiliaria,
    COUNT(t.id_transaccion) AS Operaciones_Exitosas,
    SUM(t.monto_operacion) AS Total_Facturado_Inmuebles,
    SUM(t.fee_plataforma_cim) AS Aporte_a_CIM_IA
FROM socios_inmobiliarios s
JOIN transacciones_comisiones t ON s.id_socio = t.id_socio
WHERE t.estado_pago = 'COMPLETADO'
GROUP BY s.id_socio
ORDER BY Operaciones_Exitosas DESC, Total_Facturado_Inmuebles DESC
LIMIT 5;
SELECT 
    s.nombre_comercial AS Inmobiliaria,
    p.nombre AS Plan_Actual,
    p.limite_propiedades AS Limite_Permitido,
    COUNT(pr.id_propiedad) AS Propiedades_Publicadas,
    (p.limite_propiedades - COUNT(pr.id_propiedad)) AS Cupos_Disponibles
FROM socios_inmobiliarios s
JOIN planes_saas p ON s.id_plan_actual = p.id_plan
LEFT JOIN propiedades pr ON s.id_socio = pr.id_socio AND pr.estado = 'DISPONIBLE'
GROUP BY s.id_socio
HAVING p.limite_propiedades > 0 -- Solo analiza los que tienen límite (Plan Básico)
ORDER BY Cupos_Disponibles ASC;