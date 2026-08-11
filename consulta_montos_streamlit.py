import streamlit as st
import pandas as pd
import os
import time

# =========================
# Config / Constantes
# =========================
FILE_PATH = "CIERRE_PPTO_2025.xlsx"
SHEET_NAME = "bases"

# Traductor de días y meses al español
dias_es = {
    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
}

meses_es = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

# =========================
# Helpers
# =========================
def formatear_monto(valor):
    try:
        valor = int(valor)
    except:
        valor = 0
    return f"${valor:,.0f}".replace(",", ".")


def to_int(v):
    """Convierte a int de forma robusta (soporta strings con puntos/comas)."""
    if pd.isna(v):
        return 0
    if isinstance(v, str):
        v = v.replace(".", "").replace(",", ".").strip()
    try:
        return int(float(v))
    except:
        return 0


def tarjeta(icono, titulo, monto, clase):
    return f"""
    <div class="metric-card {clase}">
        <div class="metric-icon">{icono}</div>
        <div class="metric-title">{titulo}</div>
        <div class="metric-value">{formatear_monto(monto)}</div>
        <div class="metric-caption">Total del día</div>
    </div>
    """


# =========================
# Data load
# =========================
@st.cache_data
def load_data(file_path: str, mtime: float):
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(xls, sheet_name=SHEET_NAME)

    # La primera fila trae los nombres reales de columnas
    df.columns = df.iloc[0]
    df = df[1:].copy()

    # Limpiar nombres de columnas
    df.columns = [str(c).strip() for c in df.columns]

    # Renombrar a nombres consistentes
    df.rename(columns={
        "dia": "Fecha",
        "WIN TGM": "Win TGM",
        "COIN IN": "Coin In",
        "WIN MESAS": "Win Mesas",
        "DROP": "Drop Mesas"
    }, inplace=True)

    # Convertir Fecha robusto (formato chileno) + eliminar hora
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce", dayfirst=True).dt.normalize()

    return df


# =========================
# UI / Estilo
# =========================
st.set_page_config(page_title="PPTO Enjoy Los Ángeles", page_icon="📊", layout="centered")

st.markdown("""
<style>
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }

    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }

    .date-title {
        font-size: 1.55rem;
        font-weight: 750;
        margin: 1.2rem 0 1rem 0;
    }

    .metric-card {
        border-radius: 20px;
        padding: 1.25rem;
        min-height: 190px;
        border: 1px solid rgba(255,255,255,0.10);
        box-shadow: 0 10px 30px rgba(0,0,0,0.18);
        margin-bottom: 1rem;
    }

    .metric-icon {
        font-size: 2.2rem;
        margin-bottom: 1rem;
    }

    .metric-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 0.55rem;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 850;
        line-height: 1.1;
        margin-bottom: 0.65rem;
        letter-spacing: -0.02em;
    }

    .metric-caption {
        color: #a8b0bd;
        font-size: 0.95rem;
    }

    .tgm {
        background: linear-gradient(145deg, rgba(12,72,50,0.40), rgba(7,26,22,0.72));
        border-bottom: 3px solid #28c76f;
    }
    .tgm .metric-value { color: #38d879; }

    .coin {
        background: linear-gradient(145deg, rgba(20,55,95,0.45), rgba(8,23,42,0.76));
        border-bottom: 3px solid #4097ff;
    }
    .coin .metric-value { color: #4c9cff; }

    .mesas {
        background: linear-gradient(145deg, rgba(70,42,105,0.42), rgba(25,19,42,0.76));
        border-bottom: 3px solid #ad55ff;
    }
    .mesas .metric-value { color: #b45eff; }

    .drop {
        background: linear-gradient(145deg, rgba(90,72,22,0.38), rgba(34,30,17,0.76));
        border-bottom: 3px solid #f1be28;
    }
    .drop .metric-value { color: #f2be2d; }

    .info-box {
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.035);
        border-radius: 16px;
        padding: 1rem 1.15rem;
        color: #c7ced8;
        margin-top: 0.4rem;
        font-size: 0.95rem;
    }

    div[data-testid="stDateInput"] input {
        border-radius: 14px;
    }

    @media (max-width: 640px) {
        .main-title { font-size: 2.15rem; }
        .date-title { font-size: 1.3rem; }
        .metric-card { min-height: 165px; padding: 1rem; }
        .metric-value { font-size: 1.6rem; }
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 PPTO</div>', unsafe_allow_html=True)

# Botón para forzar recarga
colA, colB = st.columns([1, 3])
with colA:
    if st.button("🔄 Recargar"):
        st.cache_data.clear()
        st.rerun()

with colB:
    if os.path.exists(FILE_PATH):
        st.caption(
            f"Actualizado: {time.strftime('%d/%m/%Y %H:%M', time.localtime(os.path.getmtime(FILE_PATH)))}"
        )

# Selección de fecha
st.markdown("📆 **Selecciona una fecha (formato: día/mes/año):**")
fecha = st.date_input("", format="DD/MM/YYYY", label_visibility="collapsed")

# Mostrar fecha formateada
dia_semana = dias_es.get(fecha.strftime('%A'), fecha.strftime('%A'))
dia = fecha.day
mes = meses_es.get(fecha.month, str(fecha.month))
anio = fecha.year
st.markdown(
    f'<div class="date-title">📅 {dia_semana} {dia:02d} de {mes} de {anio}</div>',
    unsafe_allow_html=True
)

try:
    if not os.path.exists(FILE_PATH):
        raise FileNotFoundError

    mtime = os.path.getmtime(FILE_PATH)
    df = load_data(FILE_PATH, mtime)

    # Filtro robusto: compara por día (ignora hora)
    df_filtrado = df[df["Fecha"].dt.date == fecha]

    if not df_filtrado.empty:
        if len(df_filtrado) > 1:
            st.warning(f"⚠️ Hay {len(df_filtrado)} filas para esta fecha. Se mostrará la primera.")

        fila = df_filtrado.iloc[0]

        win_tgm = to_int(fila.get("Win TGM"))
        coin_in = to_int(fila.get("Coin In"))
        win_mesas = to_int(fila.get("Win Mesas"))
        drop_mesas = to_int(fila.get("Drop Mesas"))

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(tarjeta("🎰", "Win TGM", win_tgm, "tgm"), unsafe_allow_html=True)
        with col2:
            st.markdown(tarjeta("💵", "Coin In", coin_in, "coin"), unsafe_allow_html=True)

        col3, col4 = st.columns(2)
        with col3:
            st.markdown(tarjeta("🎲", "Win Mesas", win_mesas, "mesas"), unsafe_allow_html=True)
        with col4:
            st.markdown(tarjeta("🪙", "Drop Mesas", drop_mesas, "drop"), unsafe_allow_html=True)

        actualizado = time.strftime('%d/%m/%Y %H:%M', time.localtime(os.path.getmtime(FILE_PATH)))
        st.markdown(
            f'<div class="info-box">ℹ️ Los montos están expresados en pesos chilenos (CLP).<br>'
            f'<span style="color:#8f98a6;">Actualizado: {actualizado}</span></div>',
            unsafe_allow_html=True
        )

    else:
        st.warning("⚠️ No se encontraron datos para la fecha seleccionada.")

except FileNotFoundError:
    st.error("❌ El archivo 'CIERRE_PPTO_2025.xlsx' no se encontró.")
except Exception as e:
    st.error(f"❌ Error: {e}")
