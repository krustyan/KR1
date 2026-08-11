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
        padding-top: 0.7rem;
        padding-bottom: 1rem;
        max-width: 760px;
    }

    .main-title {
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 0.25rem 0;
        letter-spacing: -0.02em;
    }

    .date-title {
        font-size: 1.25rem;
        font-weight: 750;
        margin: 0.65rem 0 0.65rem 0;
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.65rem;
        width: 100%;
    }

    .metric-card {
        border-radius: 16px;
        padding: 0.85rem;
        min-height: 122px;
        border: 1px solid rgba(255,255,255,0.10);
        box-shadow: 0 6px 18px rgba(0,0,0,0.16);
        display: flex;
        flex-direction: column;
        justify-content: center;
        overflow: hidden;
    }

    .metric-icon {
        font-size: 1.6rem;
        line-height: 1;
        margin-bottom: 0.55rem;
    }

    .metric-title {
        font-size: 0.95rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
        white-space: nowrap;
    }

    .metric-value {
        font-size: clamp(1.05rem, 4.8vw, 1.65rem);
        font-weight: 850;
        line-height: 1.08;
        letter-spacing: -0.035em;
        white-space: nowrap;
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
        border-radius: 12px;
        padding: 0.65rem 0.8rem;
        color: #aeb6c2;
        margin-top: 0.65rem;
        font-size: 0.78rem;
        line-height: 1.35;
    }

    div[data-testid="stDateInput"] input {
        border-radius: 12px;
    }

    div[data-testid="stDateInput"] {
        margin-bottom: -0.35rem;
    }

    div[data-testid="stButton"] button {
        padding-top: 0.25rem;
        padding-bottom: 0.25rem;
        min-height: 2.2rem;
    }

    @media (max-width: 640px) {
        .block-container {
            padding-left: 0.8rem;
            padding-right: 0.8rem;
            padding-top: 0.45rem;
        }

        .main-title {
            font-size: 1.7rem;
        }

        .date-title {
            font-size: 1.05rem;
            margin: 0.5rem 0 0.55rem 0;
        }

        .metric-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.5rem;
        }

        .metric-card {
            min-height: 108px;
            border-radius: 14px;
            padding: 0.7rem;
        }

        .metric-icon {
            font-size: 1.35rem;
            margin-bottom: 0.4rem;
        }

        .metric-title {
            font-size: 0.82rem;
            margin-bottom: 0.28rem;
        }

        .metric-value {
            font-size: clamp(0.93rem, 4.35vw, 1.25rem);
        }

        .info-box {
            font-size: 0.72rem;
            padding: 0.55rem 0.65rem;
            margin-top: 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 PPTO</div>', unsafe_allow_html=True)

# Recarga compacta
colA, colB = st.columns([1, 2.2])
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
st.markdown("📆 **Selecciona una fecha:**")
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

        # Grid HTML propio para mantener 2 columnas también en teléfono
        tarjetas_html = f"""
        <div class="metric-grid">
            {tarjeta("🎰", "Win TGM", win_tgm, "tgm")}
            {tarjeta("💵", "Coin In", coin_in, "coin")}
            {tarjeta("🎲", "Win Mesas", win_mesas, "mesas")}
            {tarjeta("🪙", "Drop Mesas", drop_mesas, "drop")}
        </div>
        """
        st.markdown(tarjetas_html, unsafe_allow_html=True)

        actualizado = time.strftime('%d/%m/%Y %H:%M', time.localtime(os.path.getmtime(FILE_PATH)))
        st.markdown(
            f'<div class="info-box">ℹ️ Montos en pesos chilenos (CLP) · Actualizado: {actualizado}</div>',
            unsafe_allow_html=True
        )

    else:
        st.warning("⚠️ No se encontraron datos para la fecha seleccionada.")

except FileNotFoundError:
    st.error("❌ El archivo 'CIERRE_PPTO_2025.xlsx' no se encontró.")
except Exception as e:
    st.error(f"❌ Error: {e}")
