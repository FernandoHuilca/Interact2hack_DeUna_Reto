import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import random
import base64
from pathlib import Path

import joblib
from diagnostico import generar_diagnostico

# Cargar modelo y SHAP values (una sola vez, cached)
@st.cache_resource
def cargar_recursos():
    return {
        "shap_df":   pd.read_csv("shap_values.csv"),
        "df_orig":   pd.read_csv("deuna2.csv"),   # datos crudos con id_comercio
        "modelo":    joblib.load("modelo_RF_churn.joblib"),
        "scaler":    joblib.load("scaler_churn.joblib"),
    }

recursos = cargar_recursos()

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="De Una Dashboard - Churn",
    page_icon="🟣",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# GLOBAL CSS  (paleta + tipografía)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lilita+One&family=Montserrat:wght@400;500;600;700;800;900&display=swap');

:root {
    --morado:       #4d2973;
    --morado-claro: #ece8f7;
    --morado-medio: #a478d1;
    --verde:        #64bda1;
    --verde-claro:  #a5efce;
    --amarillo:     #fcb632;
    --blanco:       #ffffff;
    --negro:        #000000;
    --gris:         #4f5563;
}

/* fondo general */
.stApp {
    background-color: var(--morado-claro);
    font-family: 'Montserrat', sans-serif;
}

/* ── HEADER ── */
.header-bar {
    background: var(--morado);
    border-radius: 16px;
    padding: 18px 32px;
    display: flex;
    align-items: center;
    gap: 24px;
    margin-bottom: 24px;
    box-shadow: 0 4px 18px rgba(77,41,115,.35);
}
.header-logo {
    width: 72px;
    height: 72px;
    border-radius: 14px;
    object-fit: cover;
    border: 3px solid var(--morado-medio);
}
.header-title {
    font-family: 'Lilita One', cursive;
    font-weight: 400;
    font-size: 2.4rem;
    color: var(--blanco);
    line-height: 1.1;
    margin: 0;
}
.header-sub {
    font-family: 'Montserrat', sans-serif;
    font-weight: 500;
    color: var(--morado-medio);
    font-size: 1rem;
    margin-top: 4px;
}

/* ── KPI CARDS ── */
.kpi-card {
    background: var(--blanco);
    border-radius: 14px;
    padding: 20px 24px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(77,41,115,.12);
    border-top: 4px solid var(--morado);
}
.kpi-value {
    font-family: 'Lilita One', cursive;
    font-weight: 400;
    font-size: 2.2rem;
    color: var(--morado);
}
.kpi-label {
    font-family: 'Montserrat', sans-serif;
    font-size: 0.85rem;
    color: var(--gris);
    margin-top: 4px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .05em;
}

/* ── SECTION TITLES ── */
.section-title {
    font-family: 'Lilita One', cursive;
    font-weight: 400;
    font-size: 1.5rem;
    color: var(--morado);
    border-left: 5px solid var(--morado-medio);
    padding-left: 12px;
    margin: 28px 0 16px 0;
}

/* ── FILTER BAR ── */
.filter-bar {
    background: var(--blanco);
    border-radius: 14px;
    padding: 18px 24px;
    box-shadow: 0 2px 10px rgba(77,41,115,.1);
    margin-bottom: 18px;
}

/* ── BADGE RISK ── */
.badge-alto   { background:#fde8e8; color:#c0392b; border-radius:8px; padding:3px 10px; font-size:.8rem; font-weight:700; }
.badge-medio  { background:#fff3cd; color:#856404; border-radius:8px; padding:3px 10px; font-size:.8rem; font-weight:700; }
.badge-bajo   { background:#d4edda; color:#155724; border-radius:8px; padding:3px 10px; font-size:.8rem; font-weight:700; }

/* ── DETAIL CARDS ── */
.detail-card {
    background: var(--blanco);
    border-radius: 14px;
    padding: 22px 28px;
    box-shadow: 0 2px 12px rgba(77,41,115,.13);
    margin-bottom: 16px;
}
.detail-card h4 {
    font-family: 'Lilita One', cursive;
    font-weight: 400;
    color: var(--morado);
    margin-bottom: 10px;
}
.rec-item {
    font-family: 'Montserrat', sans-serif;
    background: var(--morado-claro);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    border-left: 4px solid var(--morado-medio);
    font-size: .9rem;
    color: var(--gris);
}

/* hide default streamlit header/footer */
#MainMenu, footer, header { visibility: hidden; }

/* bring first block (header) closer to the very top */
div.block-container { padding-top: 0.6rem; }

/* dataframe scroll */
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATOS SINTÉTICOS
# ─────────────────────────────────────────────
PROVINCIAS = [
    "Azuay","Bolívar","Cañar","Carchi","Chimborazo","Cotopaxi",
    "El Oro","Esmeraldas","Galápagos","Guayas","Imbabura","Loja",
    "Los Ríos","Manabí","Morona Santiago","Napo","Orellana",
    "Pastaza","Pichincha","Santa Elena","Santo Domingo",
    "Sucumbíos","Tungurahua","Zamora Chinchipe"
]

random.seed(42)
np.random.seed(42)

def gen_comercios(n=180):
    tipos = ["Restaurante","Farmacia","Tienda","Supermercado","Ferretería",
             "Ropa","Electrónica","Papelería","Panadería","Veterinaria"]
    riesgos = np.random.choice(["Alto","Medio","Bajo"], n, p=[.25,.40,.35])
    rows = []
    for i in range(n):
        prov = random.choice(PROVINCIAS)
        r = riesgos[i]
        tipo = random.choice(tipos)
        score = {"Alto": random.randint(70,99),
                 "Medio": random.randint(40,69),
                 "Bajo": random.randint(5,39)}[r]
        rows.append({
            "ID": f"COM-{1000+i}",
            "Comercio": f"{tipo} {random.choice(['Norte','Sur','Centro','Plaza','Real','Elite','Express'])}",
            "TipoComercio": tipo,
            "Provincia": prov,
            "Propietario": random.choice(["Ana López","Carlos Ruiz","María Pérez","Juan Torres",
                                           "Sofía Mora","Pedro Vega","Lucía Castro","Andrés Gil"]),
            "Numero celular": f"09{random.randint(10000000, 99999999)}",
            "Nivel de Riesgo": r,
            "Score Churn": score,
            "dias_sin_transar": random.randint(0, 45),
            "Transacciones (30d)": random.randint(20, 800),
            "Monto Promedio ($)": round(random.uniform(5, 420), 2),
            "Alertas Activas": random.randint(0, 8),
            "Último Análisis": pd.Timestamp("2025-01-01") + pd.to_timedelta(random.randint(0,364), unit="d"),
        })
    return pd.DataFrame(rows)

df_raw = gen_comercios(180)

# color semáforo por provincia
def provincia_riesgo(df):
    grp = df.groupby("Provincia")["Nivel de Riesgo"].value_counts(normalize=True).unstack(fill_value=0)
    for c in ["Alto","Medio","Bajo"]:
        if c not in grp.columns:
            grp[c] = 0
    def semaforo(row):
        if row.get("Alto", 0) >= 0.30: return "Alto"
        if row.get("Medio", 0) >= 0.45: return "Medio"
        return "Bajo"
    grp["semaforo"] = grp.apply(semaforo, axis=1)
    return grp["semaforo"].to_dict()

prov_semaforo = provincia_riesgo(df_raw)

# ─────────────────────────────────────────────
# GEOJSON Ecuador provincias (simplificado, coordenadas representativas)
# ─────────────────────────────────────────────
# Mapa coroplético usando scatter_geo con coordenadas centroides
PROV_COORDS = {
    "Azuay":           (-2.897, -78.993),
    "Bolívar":         (-1.601, -79.003),
    "Cañar":           (-2.558, -78.938),
    "Carchi":          (0.603,  -77.917),
    "Chimborazo":      (-1.665, -78.654),
    "Cotopaxi":        (-0.944, -78.616),
    "El Oro":          (-3.259, -79.959),
    "Esmeraldas":      (0.969,  -79.652),
    "Galápagos":       (-0.966, -90.964),
    "Guayas":          (-2.189, -79.888),
    "Imbabura":        (0.356,  -78.122),
    "Loja":            (-3.999, -79.204),
    "Los Ríos":        (-1.023, -79.460),
    "Manabí":          (-1.054, -80.452),
    "Morona Santiago": (-2.302, -78.114),
    "Napo":            (-0.995, -77.813),
    "Orellana":        (-0.459, -76.997),
    "Pastaza":         (-1.518, -78.003),
    "Pichincha":       (-0.229, -78.524),
    "Santa Elena":     (-2.226, -80.858),
    "Santo Domingo":   (-0.254, -79.172),
    "Sucumbíos":       (0.086,  -76.888),
    "Tungurahua":      (-1.253, -78.624),
    "Zamora Chinchipe":(-4.065, -78.950),
}

COLOR_MAP = {"Alto": "#e74c3c", "Medio": "#fcb632", "Bajo": "#64bda1"}


def get_logo_base64() -> str:
    logo_path = Path(__file__).resolve().parent / "Images" / "Deuna!_icono.svg.png"
    if not logo_path.exists():
        return ""
    return base64.b64encode(logo_path.read_bytes()).decode("utf-8")

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
logo_base64 = get_logo_base64()
logo_html = (
    f'<img class="header-logo" src="data:image/png;base64,{logo_base64}" alt="Deuna logo">'
    if logo_base64 else
    '<div class="header-logo" style="display:flex;align-items:center;justify-content:center;'
    'background:#4d2973;color:#64bda1;font-family:Lilita One,cursive;font-size:1.7rem;">d!</div>'
)

header_html = (
    '<div class="header-bar" style="justify-content:space-between;align-items:center;">'
    '<div style="display:flex;align-items:center;gap:18px;">'
    f'{logo_html}'
    '<div>'
    '<p style="font-family:Lilita One,cursive;font-weight:400;'
    'font-size:1.9rem;color:#64bda1;margin:0;line-height:1.1;letter-spacing:.5px;">Deuna Dashboard</p>'
    '<p style="font-family:Montserrat,sans-serif;font-weight:500;font-size:0.88rem;color:#ece8f7;margin:4px 0 0 0;letter-spacing:.04em;">'
    'Detección de Riesgo Comercial</p>'
    '</div>'
    '</div>'
    '<div style="background:#1a0a2e;border:2px solid #a478d1;border-radius:10px;'
    'padding:8px 18px;text-align:center;line-height:1.2;">'
    '<span style="font-family:Montserrat,sans-serif;font-weight:800;font-size:0.95rem;'
    'color:#a478d1;letter-spacing:2px;display:block;">INTERACT</span>'
    '<span style="font-family:Montserrat,sans-serif;font-weight:900;font-size:1.4rem;'
    'color:#64bda1;letter-spacing:1px;display:block;">2HACK</span>'
    '<span style="font-family:Montserrat,sans-serif;font-size:0.65rem;color:#ece8f7;letter-spacing:1px;">HACKATHON 2026</span>'
    '</div>'
    '</div>'
)
st.markdown(header_html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SECCIÓN 1 — RESUMEN EJECUTIVO
# ─────────────────────────────────────────────
st.markdown('<p class="section-title">Resumen Ejecutivo - Historico</p>', unsafe_allow_html=True)

# KPIs
total = len(df_raw)
alto  = (df_raw["Nivel de Riesgo"] == "Alto").sum()
medio = (df_raw["Nivel de Riesgo"] == "Medio").sum()
bajo  = (df_raw["Nivel de Riesgo"] == "Bajo").sum()
alertas_total = df_raw["Alertas Activas"].sum()
score_prom = df_raw["Score Churn"].mean()
capital_en_riesgo = 7 * (alto + medio)
temperatura_portafolio = df_raw["dias_sin_transar"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
for col, val, lbl, color in [
    (k1, total,          "Total Comercios",    "#4d2973"),
    (k2, f"${capital_en_riesgo:,.0f}", "Capital en Riesgo", "#e74c3c"),
    (k3, int(alertas_total), "Tickets de Soporte", "#a478d1"),
    (k4, f"{temperatura_portafolio:.1f} días", "Temperatura", "#fcb632"),
    (k5, f"{score_prom:.1f}", "Churn Promedio", "#4f5563"),
]:
    col.markdown(f"""
    <div class="kpi-card" style="border-top-color:{color};">
        <div class="kpi-value" style="color:{color};">{val}</div>
        <div class="kpi-label">{lbl}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Mapa + Pie
map_col, pie_col = st.columns([3, 2])

with map_col:
    st.markdown(
        '<div style="background:#ffffff;border-radius:16px;padding:22px 22px 14px 22px;'
        'box-shadow:0 4px 20px rgba(77,41,115,.13);">'
        '<p style="font-family:Lilita One,cursive;font-weight:400;'
        'font-size:1.15rem;color:#4d2973;margin:0 0 2px 0;">Mapa de Riesgo Nacional</p>'
        '<p style="font-family:Montserrat,sans-serif;font-size:.78rem;color:#a478d1;margin:0 0 14px 0;letter-spacing:.05em;">'
        'Distribución geográfica de comercios por nivel de riesgo</p>',
        unsafe_allow_html=True
    )

    # Usar coordenadas reales de cada comercio (con dispersión por provincia)
    map_df = df_raw.copy()
    map_df["lat"] = map_df["Provincia"].map(lambda p: PROV_COORDS.get(p, (-1.8, -78.5))[0])
    map_df["lon"] = map_df["Provincia"].map(lambda p: PROV_COORDS.get(p, (-1.8, -78.5))[1])
    # Pequeña dispersión para que no se apilen todos en el mismo punto
    rng = np.random.default_rng(99)
    map_df["lat"] = map_df["lat"] + rng.normal(0, 0.18, len(map_df))
    map_df["lon"] = map_df["lon"] + rng.normal(0, 0.18, len(map_df))

    fig_map = px.scatter_mapbox(
        map_df,
        lat="lat", lon="lon",
        color="Nivel de Riesgo",
        color_discrete_map={"Alto": "#e74c3c", "Medio": "#fcb632", "Bajo": "#64bda1"},
        size="Score Churn",
        size_max=14,
        hover_name="Comercio",
        hover_data={"Provincia": True, "Score Churn": True,
                    "Nivel de Riesgo": True, "lat": False, "lon": False},
        mapbox_style="carto-positron",
        zoom=5.4,
        center={"lat": -1.83, "lon": -78.18},
    )
    fig_map.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            title="Nivel de Riesgo",
            orientation="h", y=-0.06, x=0,
            font=dict(size=11, color="#4d2973"),
            bgcolor="rgba(255,255,255,0.7)",
            bordercolor="#ece8f7", borderwidth=1,
        ),
        height=420,
    )
    st.markdown(
        '<div style="height:10px;border-top:1px solid #ece8f7;margin:6px 0 12px 0;"></div>',
        unsafe_allow_html=True
    )
    st.plotly_chart(fig_map, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with pie_col:
    st.markdown(
        '<div style="background:#ffffff;border-radius:16px;padding:30px 28px 24px 28px;'
        'box-shadow:0 4px 20px rgba(77,41,115,.13);">'
        '<p style="font-family:Lilita One,cursive;font-weight:400;'
        'font-size:1.15rem;color:#4d2973;margin:0 0 2px 0;">&#9685; Distribución de Riesgo</p>'
        '<p style="font-family:Montserrat,sans-serif;font-size:.78rem;color:#a478d1;margin:0 0 16px 0;letter-spacing:.05em;">'
        'Total de comercios analizados</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div style="height:12px;border-top:1px solid #ece8f7;margin:2px 0 14px 0;"></div>',
        unsafe_allow_html=True
    )

    donut_c, metrics_c = st.columns([1.2, 0.8], gap="medium")

    with donut_c:
        total_pie = alto + medio + bajo
        pct_alto  = round(alto  / total_pie * 100, 1)
        pct_medio = round(medio / total_pie * 100, 1)
        pct_bajo  = round(bajo  / total_pie * 100, 1)

        fig_pie = px.pie(
            values=[alto, medio, bajo],
            names=["Alto", "Medio", "Bajo"],
            color=["Alto", "Medio", "Bajo"],
            color_discrete_map={"Alto": "#e74c3c", "Medio": "#fcb632", "Bajo": "#64bda1"},
            hole=0.55,
        )
        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent+label",
            textfont=dict(size=11, color="white"),
            marker=dict(line=dict(color="#ffffff", width=3)),
            hovertemplate="<b>%{label}</b><br>%{value} comercios<br>%{percent}<extra></extra>",
        )
        fig_pie.add_annotation(
            text=f"<b>{total_pie}</b>",
            x=0.5, y=0.56,
            font=dict(size=28, color="#4d2973", family="Lilita One"),
            showarrow=False,
        )
        fig_pie.add_annotation(
            text="comercios",
            x=0.5, y=0.40,
            font=dict(size=10, color="#a478d1"),
            showarrow=False,
        )
        fig_pie.update_layout(
            showlegend=False,
            margin=dict(l=8, r=8, t=18, b=12),
            paper_bgcolor="rgba(236,232,247,0.45)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=305,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with metrics_c:
        st.markdown("<br>", unsafe_allow_html=True)

        metricas = [
            (" Total comercio alto",  f"{alto}",  "#e74c3c"),
            (" Total comercio medio", f"{medio}", "#fcb632"),
            (" Total comercio bajo",  f"{bajo}",  "#64bda1"),
        ]
        for label, valor, color in metricas:
            st.markdown(
                f'<div style="margin-bottom:14px;">'
                f'<p style="font-family:Montserrat,sans-serif;font-size:.78rem;color:#a478d1;margin:0;letter-spacing:.04em;">{label}</p>'
                f'<p style="font-family:Lilita One,cursive;font-weight:400;'
                f'font-size:1.45rem;color:{color};margin:2px 0 0 0;line-height:1.1;">{valor}</p>'
                f'<div style="height:3px;width:40px;background:{color};border-radius:99px;margin-top:4px;'
                f'opacity:.5;"></div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SECCIÓN 2 — EXPLORACIÓN Y DETALLE
# ─────────────────────────────────────────────
st.markdown('<p class="section-title"> Exploración de Comercios</p>', unsafe_allow_html=True)

# Layout: filtros izquierda | tabla derecha
filter_col, table_col = st.columns([1, 3], gap="medium")

with filter_col:
    st.markdown("""
    <div style="background:white; border-radius:14px; padding:20px 18px;
                box-shadow:0 2px 10px rgba(77,41,115,.12);
                border-top:4px solid #4d2973;">
        <p style="font-family:'Lilita One',cursive;
                  font-weight:400; color:#4d2973; font-size:1.1rem; margin-bottom:16px;">
              Filtros
        </p>
    </div>
    """, unsafe_allow_html=True)

    provincias_sel = st.multiselect(
        "Provincia",
        options=sorted(PROVINCIAS),
        default=[],
        placeholder="Todas las provincias",
    )

    riesgo_sel = st.multiselect(
        "Nivel de Riesgo",
        options=["Alto", "Medio", "Bajo"],
        default=[],
        placeholder="Todos los niveles",
    )

    score_range = st.slider("Score Churn", 0, 100, (0, 100))

    st.markdown("<br>", unsafe_allow_html=True)

    # Mini resumen de filtros activos
    filtros_activos = []
    if provincias_sel:
        filtros_activos.append(f"**{len(provincias_sel)}** provincia(s)")
    if riesgo_sel:
        filtros_activos.append(f"Riesgo: {', '.join(riesgo_sel)}")
    if score_range != (0, 100):
        filtros_activos.append(f"Score: {score_range[0]}–{score_range[1]}")

    if filtros_activos:
        st.markdown(
            "<div style='background:#ece8f7;border-radius:10px;padding:10px 14px;"
            "font-size:.83rem;color:#4d2973;border-left:3px solid #a478d1;'>"
            "Filtros activos:<br>" + "<br>".join(f"• {f}" for f in filtros_activos) +
            "</div>", unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='background:#ece8f7;border-radius:10px;padding:10px 14px;"
            "font-size:.83rem;color:#a478d1;'>"
            "Sin filtros aplicados — mostrando todos los comercios."
            "</div>", unsafe_allow_html=True
        )

# Filtrado
df_filtered = df_raw.copy()
if provincias_sel:
    df_filtered = df_filtered[df_filtered["Provincia"].isin(provincias_sel)]
if riesgo_sel:
    df_filtered = df_filtered[df_filtered["Nivel de Riesgo"].isin(riesgo_sel)]
df_filtered = df_filtered[
    df_filtered["Score Churn"].between(score_range[0], score_range[1])
]

with table_col:
    st.markdown(
        f"<p style='color:#4f5563;font-size:.9rem;margin-bottom:8px;'>"
        f"<b>{len(df_filtered)}</b> comercios encontrados</p>",
        unsafe_allow_html=True
    )

    # ── TABLA ──
    display_df = df_filtered.reset_index(drop=True).copy()
    display_df["TipoComercio"] = display_df["Comercio"].str.split().str[0]
    display_df = display_df.rename(columns={
        "TipoComercio": "Tipo comercio",
        "Nivel de Riesgo": "Nivel de riesgo",
        "Score Churn": "Score churn",
        "Alertas Activas": "Ticket no resuelto",
        "Transacciones (30d)": "Numero de Transacciones",
    })

    display_cols = [
        "Tipo comercio",
        "Provincia",
        "Propietario",
        "Nivel de riesgo",
        "Score churn",
        "Ticket no resuelto",
        "Numero de Transacciones",
    ]

    event = st.dataframe(
        display_df[display_cols],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Score churn": st.column_config.ProgressColumn(
                "Score churn", min_value=0, max_value=100, format="%d"),
            "Ticket no resuelto": st.column_config.NumberColumn(
                "Ticket no resuelto", help="Tickets pendientes de resolución"),
            "Nivel de riesgo": st.column_config.TextColumn("Nivel de riesgo"),
        },
        height=380,
    )

# ─────────────────────────────────────────────
# SECCIÓN 3 — DETALLE DEL COMERCIO SELECCIONADO
# ─────────────────────────────────────────────
selected_rows = event.selection.rows if event.selection else []

# ── En la sección de detalle del comercio seleccionado ─────────
if selected_rows:
    idx = selected_rows[0]
    row = df_filtered.reset_index(drop=True).iloc[idx]
    comercio_id = row["ID"]  # ajusta al nombre de columna que usas en df_raw

    diagnostico, acciones, top_features = generar_diagnostico(
        id_comercio=comercio_id,
        df_original=recursos["df_orig"],
        shap_df=recursos["shap_df"],
    )

    # ── Diagnóstico ────────────────────────────────────────────
    st.markdown('<div class="detail-card">', unsafe_allow_html=True)
    st.markdown("#### 🩺 Diagnóstico (explicado por el modelo)")

    for item in diagnostico:
        st.markdown(f"<div class='rec-item'>{item}</div>", unsafe_allow_html=True)

    # Mini tabla SHAP para el jurado técnico
    if top_features:
        st.markdown("**Variables más influyentes (SHAP):**")
        for f in top_features:
            barra = "🔴" if f["shap"] > 0 else "🟢"
            st.markdown(
                f"<div class='rec-item'>{barra} <b>{f['nombre']}</b> — "
                f"{f['impacto']} (SHAP: {abs(f['shap']):.3f})</div>",
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Acciones ───────────────────────────────────────────────
    st.markdown('<div class="detail-card">', unsafe_allow_html=True)
    st.markdown("#### 💡 Acciones recomendadas para el equipo comercial")
    for item in acciones:
        st.markdown(f"<div class='rec-item'>{item}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info(" Selecciona una fila de la tabla para ver el diagnóstico detallado del comercio.")


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:#a478d1; font-size:.8rem; margin-top:40px; padding:16px;
            border-top:1px solid #ece8f7;">
    De Una · Módulo Churn &nbsp;|&nbsp; Detección de Riesgo Comercial &nbsp;|&nbsp; Outliers Hackathon 2026<br>
</div>
""", unsafe_allow_html=True)