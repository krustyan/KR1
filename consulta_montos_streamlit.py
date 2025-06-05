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
    return f"${valor:,.0f}".replace(",", ".")  # separador de miles con punto

# Cargar archivo Excel desde subida del usuario
def load_data(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    df = pd.read_excel(xls, sheet_name="bases")

    headers = df.iloc[0].tolist()
    df = df.iloc[1:].copy()
    df.columns = [str(h).strip() for h in headers]
    df.columns = [c.strip() for c in df.columns]

    df.rename(columns={
        "WIN TGM": "Win TGM",
        "COIN IN": "Coin In",
        "WIN MESAS": "Win Mesas",
    }, inplace=True)

    return df

# Extraer valor por nombre de columna (seguro)
def get_val(df, col):
    if col in df.columns and not pd.isnull(df[col].iat[0]):
        return int(float(df[col].iat[0]))
    return 0

# Interfaz Streamlit
st.title("📊 Presupuesto Diario Casino Enjoy Los Ángeles")

fecha = st.date_input("Selecciona una fecha")
st.write(f"Fecha seleccionada: {fecha.strftime('%Y-%m-%d')} ({dias_es[fecha.strftime('%A')]})")

uploaded_file = st.file_uploader("Sube el archivo CIERRE_PPTO_2025.xlsx", type="xlsx")

if uploaded_file is not None:
    df = load_data(uploaded_file)

    win_tgm = get_val(df, "Win TGM")
    coin_in = get_val(df, "Coin In")
    win_mesas = get_val(df, "Win Mesas")

    st.subheader("🔍 Resumen Financiero")
    st.markdown(f"- **Win TGM:** {formatear_monto(win_tgm)}")
    st.markdown(f"- **Coin In:** {formatear_monto(coin_in)}")
    st.markdown(f"- **Win Mesas:** {formatear_monto(win_mesas)}")

    if coin_in > 0:
        payoff = win_tgm / coin_in
        st.markdown(f"- **Payoff estimado:** {payoff:.2%}")
    else:
        st.markdown("- **Payoff estimado:** No disponible (Coin In = 0)")
else:
    st.warning("Por favor, sube el archivo Excel para continuar.")


