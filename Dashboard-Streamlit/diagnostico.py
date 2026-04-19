# diagnostico.py

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
        "critico": lambda v: f"Sin transaccionar hace {int(v)} días — supera el umbral crítico de 20 días.",
        "alerta":  lambda v: f"Lleva {int(v)} días sin transaccionar — actividad en descenso.",
    },
    "tasa_tickets_no_resueltos": { # NUEVO
        "critico": lambda v: f"El {v*100:.0f}% de sus tickets no tienen solución. Causa de frustración crítica.",
        "alerta":  lambda v: f"Más del {v*100:.0f}% de sus tickets quedan sin resolver. Experiencia de soporte deficiente.",
    },
    "tickets_soporte": {
        "critico": lambda v: f"{int(v)} tickets abiertos — patrón de problemas recurrentes.",
        "alerta":  lambda v: f"{int(v)} tickets abiertos — requiere seguimiento.",
    },
    "saldo_cuenta_usd": {
        "critico": lambda v: f"Saldo de ${v:.2f} — nivel crítico, reduce compromiso con la plataforma.",
        "alerta":  lambda v: f"Saldo de ${v:.2f} — por debajo del promedio saludable.",
    },
    "transacciones_promedio": {
        "critico": lambda v: f"Solo {int(v)} transacciones promedio — actividad mínima.",
        "alerta":  lambda v: f"{int(v)} transacciones promedio — por debajo del promedio del segmento.",
    },
}

ACCIONES = {
    "Alto": [
        "📞 Llamada urgente esta semana — prioridad máxima en el portafolio del comercial.",
        "🔧 Escalar ticket pendiente a soporte nivel 2 de forma inmediata si existe.",
        "🎯 Ofrecer asesoría digital personalizada — especialmente si el propietario supera los 45 años.",
        "💡 Proponer acceso a nueva funcionalidad por 30 días como incentivo de permanencia.",
    ],
    "Medio": [
        "📱 Contacto proactivo vía WhatsApp en los próximos 7 días.",
        "🎁 Ofrecer beneficio del mes — cashback puntual o límite de transacción ampliado.",
        "📋 Gestionar cierre de tickets de soporte abiertos antes del contacto comercial.",
        "📊 Compartir reporte de rendimiento comparado con comercios similares en su provincia.",
    ],
    "Bajo": [
        "✅ Sin acción urgente — revisión en el ciclo mensual de portafolio.",
        "🏆 Considerar para programa de embajadores o referidos de De Una.",
        "📬 Incluir en campaña de fidelización preventiva del siguiente trimestre.",
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
        diagnostico = ["Comportamiento transaccional dentro de parámetros normales para este segmento."]

    return diagnostico, ACCIONES[nivel_riesgo], factores