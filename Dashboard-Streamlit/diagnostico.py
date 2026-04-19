UMBRALES = {
    "dias_sin_transar":       {"critico": 20,   "alerta": 7},
    "tasa_tickets_no_resueltos": {"critico": 0.5, "alerta": 0.25}, # NUEVA TASA
    "tickets_soporte":        {"critico": 3,    "alerta": 2},
    "saldo_cuenta_usd":       {"critico": 5.0,  "alerta": 15.0},
    "transacciones_promedio": {"critico": 5,    "alerta": 15},
}

# Para estas variables, valor BAJO es el problema
VARIABLES_INVERSION = {"saldo_cuenta_usd", "transacciones_promedio"}

NOMBRES = {
    "dias_sin_transar":       "Días sin transaccionar",
    "tasa_tickets_no_resueltos": "Tasa de tickets sin resolver", # NUEVA
    "tickets_soporte":        "Tickets de soporte abiertos",
    "saldo_cuenta_usd":       "Saldo en cuenta (USD)",
    "transacciones_promedio": "Transacciones promedio",
}

MENSAJES = {
    "dias_sin_transar": {
        "critico": lambda v: f"Sin transaccionar hace {int(v)} días: <b>supera el umbral crítico de 20 días</b>.",
        "alerta":  lambda v: f"Lleva {int(v)} días sin transaccionar: <b>actividad en descenso</b>.",
    },
    "tasa_tickets_no_resueltos": {
        "critico": lambda v: f"El {v*100:.0f}% de sus tickets <b>no tienen solución</b>. <b>Frustración crítica</b>.",
        "alerta":  lambda v: f"Más del {v*100:.0f}% de sus tickets <b>quedan sin resolver</b>. Experiencia de <b>soporte deficiente</b>.",
    },
    "tickets_soporte": {
        "critico": lambda v: f"{int(v)} tickets abiertos: <b>patrón de problemas recurrentes</b>.",
        "alerta":  lambda v: f"{int(v)} tickets abiertos: <b>requiere seguimiento</b>.",
    },
    "saldo_cuenta_usd": {
        "critico": lambda v: f"Saldo de ${v:.2f}: <b>nivel crítico</b>, reduce <b>compromiso</b> con la plataforma.",
        "alerta":  lambda v: f"Saldo de ${v:.2f}: <b>por debajo del promedio</b> saludable.",
    },
    "transacciones_promedio": {
        "critico": lambda v: f"Solo {int(v)} transacciones promedio: <b>actividad mínima</b>.",
        "alerta":  lambda v: f"{int(v)} transacciones promedio: <b>por debajo del promedio</b> del segmento.",
    },
}

ACCIONES = {
    "Alto": [
        "<b>Llamada urgente</b> esta semana: prioridad máxima en el portafolio del encargado.",
        "<b>Escalar ticket pendiente</b> a soporte técnico de forma inmediata si el caso lo amerita.",
        "<b>Ofrecer asesoría digital personalizada</b>: especialmente si el propietario supera los 45 años.",
        "<b>Proponer acceso anticipado a futuras nuevas funcionalidades</b> como incentivo de permanencia.",
    ],
    "Medio": [
        "<b>Contacto proactivo</b> vía WhatsApp en los próximos 7 días.",
        "<b>Ofrecer beneficio del mes</b>: cashback puntual o límite de transacción ampliado.",
        "<b>Gestionar cierre de tickets</b> de soporte abiertos antes del contacto comercial.",
        "<b>Realizar una propuesta para mejora de rendimiento en ventas</b> comparado con la competencia directa.",
    ],
    "Bajo": [
        "<b>Monitoreo pasivo</b>: Mantener revisión mensual mediante el dashboard.",
        "<b>Reforzar presencia en el punto de venta</b>: Asegurar mediante encuestas automatizadas que el local cuenta con material físico visible como stickers y acrílicos QR de Deuna para incentivar el pago de sus clientes.",
        "<b>Envío de reporte de valor</b>: Compartir por WhatsApp un resumen mensual automatizado de sus ventas y crecimiento con Deuna para tangibilizar el beneficio que se le da al negocio.",
        "<b>Incentivar aumento de ticket promedio</b>: Enviar tutoriales cortos o tips sobre cómo ofrecer combos o promociones a los clientes que paguen específicamente con la app.",
    ],
}

def _clasificar(variable: str, valor: float) -> str:
    if variable not in UMBRALES:
        return "ok"
    u = UMBRALES[variable]
    if variable in VARIABLES_INVERSION:
        if valor <= u["critico"]: return "critico"
        if valor <= u["alerta"]:  return "alerta"
        return "ok"
    else:
        if valor >= u["critico"]: return "critico"
        if valor >= u["alerta"]:  return "alerta"
        return "ok"

def generar_diagnostico(row: dict, nivel_riesgo: str) -> tuple:
    """
    row          : dict con los valores del comercio (fila del Excel)
    nivel_riesgo : 'Alto' | 'Medio' | 'Bajo'
    Retorna      : (diagnostico: list[str], acciones: list[str], factores: list[dict])
    """
    factores = []
    
    # --- Lógica para la nueva tasa de tickets no resueltos ---
    tickets_soporte = row.get("tickets_soporte", 0)
    ticket_no_resuelto = row.get("ticket_no_resuelto", 0)
    
    if tickets_soporte > 0:
        tasa_no_resueltos = ticket_no_resuelto / tickets_soporte
        estado_tasa = _clasificar("tasa_tickets_no_resueltos", tasa_no_resueltos)
        if estado_tasa != "ok":
            factores.append({
                "variable": "tasa_tickets_no_resueltos",
                "nombre":   NOMBRES["tasa_tickets_no_resueltos"],
                "valor":    tasa_no_resueltos,
                "estado":   estado_tasa,
                "peso":     {"critico": 3, "alerta": 2, "ok": 0}[estado_tasa], # Mayor peso
            })

    # --- Resto de variables ---
    for var in UMBRALES:
        if var == "tasa_tickets_no_resueltos": # Ya la procesamos
            continue

        valor = row.get(var)
        if valor is None:
            continue
        
        estado = _clasificar(var, float(valor))
        factores.append({
            "variable": var,
            "nombre":   NOMBRES[var],
            "valor":    valor,
            "estado":   estado,
            "peso":     {"critico": 3, "alerta": 1, "ok": 0}[estado],
        })

    factores.sort(key=lambda x: x["peso"], reverse=True)

    diagnostico = []
    for f in factores[:3]:
        if f["estado"] == "ok":
            break
        msg = MENSAJES[f["variable"]][f["estado"]](f["valor"])
        diagnostico.append(msg)

    if not diagnostico:
        diagnostico = ["<b>Comportamiento transaccional</b> dentro de <b>parámetros normales</b> para este segmento."]

    return diagnostico, ACCIONES[nivel_riesgo], factores
