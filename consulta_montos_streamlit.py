import streamlit as st
import pandas as pd
import re

# Diccionario de días en español
dias_es = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "Sábado",
    "Sunday": "Domingo"
}

# Formato CLP para mostrar
def formatear_monto(valor):
    try:
        return f"${valor:,.0f}".replace(",", ".")
    except:
        return "$0"

# Cargar datos desde el Excel
@st.cache_data
def load_data():
    xls = pd.ExcelFile("attached_assets/CIERRE_PPTO_2025_1749150043653.xlsx")
    df = pd.read_excel(xls, sheet_name="bases")

    # Limpiar encabezados
    headers = df.iloc[0].tolist()
    df = df.iloc[1:].copy()
    df.columns = [str(h).strip() for h in headers]

    # Renombrar columnas
    df.rename(columns={
        "WIN TGM": "Win TGM",
        "COIN IN": "CI TGM",
        "WIN MESAS": "Win Mesas",
        "DROP": "DROP Mesas"
    }, inplace=True)

    # Formatear fecha y día
    df.rename(columns={df.columns[0]: "fecha"}, inplace=True)
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["día_semana_en"] = df["fecha"].dt.day_name()
    df["día_semana"] = df["día_semana_en"].map(dias_es)
    df["fecha"] = df["fecha"].dt.strftime("%d/%m/%Y")

    # Convertir columnas monetarias de forma segura
    for col in ["Win TGM", "CI TGM", "Win Mesas", "DROP Mesas"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

# 🖼️ Interfaz Streamlit
st.markdown("<h1 style='text-align: center;'>📊 Presupuesto Diario Casino Enjoy Los Ángeles</h1>", unsafe_allow_html=True)

fecha_seleccionada = st.date_input("Selecciona una fecha")
df_bases = load_data()

# Buscar fila correspondiente
fila = df_bases[df_bases["fecha"] == fecha_seleccionada.strftime("%d/%m/%Y")]

if not fila.empty:
    fila = fila.iloc[0]

    st.markdown(f"### 📅 {fila['día_semana']} - {fila['fecha']}")

    st.markdown(f"### 🏧 Win TGM: <span style='color:green'>{formatear_monto(fila['Win TGM'])}</span>", unsafe_allow_html=True)
    st.markdown(f"### 🪙 CI TGM: <span style='color:green'>{formatear_monto(fila['CI TGM'])}</span>", unsafe_allow_html=True)
    st.markdown(f"### 🎲 Win Mesas: <span style='color:green'>{formatear_monto(fila['Win Mesas'])}</span>", unsafe_allow_html=True)
    st.markdown(f"### 📉 DROP Mesas: <span style='color:green'>{formatear_monto(fila['DROP Mesas'])}</span>", unsafe_allow_html=True)
else:
    st.warning("No hay información disponible para esa fecha.")

