import streamlit as st
import pandas as pd
import re

# Diccionario para traducir días al español
dias_es = {
    'Monday': 'Lunes',
    'Tuesday': 'Martes',
    'Wednesday': 'Miércoles',
    'Thursday': 'Jueves',
    'Friday': 'Viernes',
    'Saturday': 'Sábado',
    'Sunday': 'Domingo'
}

# Formato personalizado para CLP
def formatear_monto(valor):
    return f"${valor:,.0f}".replace(",", ".")

@st.cache_data
def load_data():
    xls = pd.ExcelFile("CIERRE_PPTO_2025.xlsx")
    df = pd.read_excel(xls, sheet_name="bases")

    headers = df.iloc[0].tolist()
    df = df.iloc[1:].copy()
    df.columns = [str(h).strip() for h in headers]
    df.columns = [c.strip() for c in df.columns]

    df.rename(columns={
        "WIN TGM": "Win TGM",
        "COIN IN": "Coin In",
        "WIN MESAS": "Win Mesas",
        "FECHA": "Fecha"
    }, inplace=True)

    # Convertir la columna Fecha a formato datetime
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce')

    return df

def get_val(fila, col):
    if col in fila and not pd.isnull(fila[col]):
        return int(float(fila[col]))
    return 0

# Interfaz
st.title("📈 Presupuesto Diario Casino Enjoy Los Ángeles")

fecha = st.date_input("Selecciona una fecha")
st.write(f"Fecha seleccionada: {fecha.strftime('%Y-%m-%d')} ({dias_es[fecha.strftime('%A')]})")

try:
    df = load_data()

    # Filtrar por la fecha seleccionada
    fila = df[df["Fecha"] == pd.to_datetime(fecha)]

    if not fila.empty:
        fila = fila.iloc[0]  # Tomamos la primera fila que coincide
        win_tgm = get_val(fila, "Win TGM")
        coin_in = get_val(fila, "Coin In")
        win_mesas = get_val(fila, "Win Mesas")

        st.subheader("📊 PPTO")
        st.markdown(f"🎰 **Win TGM:** {formatear_monto(win_tgm)}")
        st.markdown(f"💵 **Coin In:** {formatear_monto(coin_in)}")
        st.markdown(f"🎲 **Win Mesas:** {formatear_monto(win_mesas)}")

        if coin_in > 0:
            payoff = win_tgm / coin_in
            st.markdown(f"📈 **Payoff estimado:** {payoff:.2%}")
        else:
            st.markdown("📉 **Payoff estimado:** No disponible (Coin In = 0)")
    else:
        st.warning("⚠️ No se encontraron datos para la fecha seleccionada.")

except FileNotFoundError:
    st.error("❌ El archivo 'CIERRE_PPTO_2025.xlsx' no se encontró en el repositorio.")
