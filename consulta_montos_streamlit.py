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
    """Convierte a int de forma robusta (soporta strings con puntos/ comas)."""
    if pd.isna(v):
        return 0
    if isinstance(v, str):
        # ejemplo: "201.156.366" -> "201156366"
        v = v.replace(".", "").replace(",", ".").strip()
    try:
        return int(float(v))
    except:
        return 0

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
# UI
# =========================
st.title("📈 PPTO ENJOY LOS ÁNGELES")

# Botón para forzar recarga
colA, colB = st.columns([1, 3])
with colA:
    if st.button("🔄 Recargar datos"):
        st.cache_data.clear()
        st.rerun()

# Diagnóstico del archivo (para corroborar si se está leyendo el Excel correcto)
with colB:
    if os.path.exists(FILE_PATH):
        st.caption(
            f"📄 Leyendo: {os.path.abspath(FILE_PATH)} | "
            f"Modificado: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(FILE_PATH)))} | "
            f"Tamaño: {os.path.getsize(FILE_PATH)} bytes"
        )
    else:
        st.caption(f"📄 Archivo no encontrado en: {os.path.abspath(FILE_PATH)}")

# Selección de fecha con formato día/mes/año
st.markdown("📆 **Selecciona una fecha (formato: día/mes/año):**")
fecha = st.date_input("", format="DD/MM/YYYY")

# Mostrar fecha formateada
dia_semana = dias_es.get(fecha.strftime('%A'), fecha.strftime('%A'))
dia = fecha.day
mes = meses_es.get(fecha.month, str(fecha.month))
anio = fecha.year
st.markdown(f"📅 **{dia_semana} {dia:02d} de {mes} de {anio}**")

try:
    if not os.path.exists(FILE_PATH):
        raise FileNotFoundError

    mtime = os.path.getmtime(FILE_PATH)
    df = load_data(FILE_PATH, mtime)

    # Filtro robusto: compara por día (ignora hora)
    df_filtrado = df[df["Fecha"].dt.date == fecha]

    if not df_filtrado.empty:
        # Si hay más de 1 fila para el día, mostramos un aviso
        if len(df_filtrado) > 1:
            st.warning(f"⚠️ Hay {len(df_filtrado)} filas para esta fecha. Se mostrará la primera.")
            # Si quieres ver todas, descomenta:
            # st.dataframe(df_filtrado)

        fila = df_filtrado.iloc[0]

        win_tgm = to_int(fila.get("Win TGM"))
        coin_in = to_int(fila.get("Coin In"))
        win_mesas = to_int(fila.get("Win Mesas"))
        drop_mesas = to_int(fila.get("Drop Mesas"))

        st.subheader("📊 PPTO")
        st.markdown(f"🎰 **Win TGM:** {formatear_monto(win_tgm)}")
        st.markdown(f"💵 **Coin In:** {formatear_monto(coin_in)}")
        st.markdown(f"🎲 **Win Mesas:** {formatear_monto(win_mesas)}")
        st.markdown(f"🪙 **Drop Mesas:** {formatear_monto(drop_mesas)}")

    else:
        st.warning("⚠️ No se encontraron datos para la fecha seleccionada.")

        # Debug opcional: ver rango real de fechas
        # st.write("Rango de fechas:", df["Fecha"].min(), df["Fecha"].max())
        # st.write("Ejemplos:", df["Fecha"].dropna().head(10))

except FileNotFoundError:
    st.error("❌ El archivo 'CIERRE_PPTO_2025.xlsx' no se encontró.")
except Exception as e:
    st.error(f"❌ Error: {e}")
