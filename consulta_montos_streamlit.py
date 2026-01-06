import streamlit as st
import pandas as pd

# Traductor de días y meses al español
dias_es = {
    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
}

meses_es = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

def formatear_monto(valor):
    try:
        valor = int(valor)
    except:
        valor = 0
    return f"${valor:,.0f}".replace(",", ".")

@st.cache_data
def load_data():
    xls = pd.ExcelFile("CIERRE_PPTO_2025.xlsx")
    df = pd.read_excel(xls, sheet_name="bases")

    # La primera fila trae los nombres reales de columnas
    df.columns = df.iloc[0]
    df = df[1:].copy()

    # Limpiar nombres de columnas (por espacios, saltos raros, etc.)
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

def get_val(fila, col):
    if col in fila and not pd.isnull(fila[col]):
        try:
            return int(float(fila[col]))
        except:
            return 0
    return 0

# Interfaz principal
st.title("📈 PPTO ENJOY LOS ÁNGELES")

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
    df = load_data()

    # ✅ Filtro robusto: compara por día (ignora hora)
    df_filtrado = df[df["Fecha"].dt.date == fecha]

    if not df_filtrado.empty:
        fila = df_filtrado.iloc[0]
        win_tgm = get_val(fila, "Win TGM")
        coin_in = get_val(fila, "Coin In")
        win_mesas = get_val(fila, "Win Mesas")
        drop_mesas = get_val(fila, "Drop Mesas")

        st.subheader("📊 PPTO")
        st.markdown(f"🎰 **Win TGM:** {formatear_monto(win_tgm)}")
        st.markdown(f"💵 **Coin In:** {formatear_monto(coin_in)}")

        if coin_in > 0:
            payoff = win_tgm / coin_in
            st.markdown(f"📈 **Payoff estimado:** {payoff:.2%}")
        else:
            st.markdown("📉 **Payoff estimado:** No disponible (Coin In = 0)")

        st.markdown(f"🎲 **Win Mesas:** {formatear_monto(win_mesas)}")
        st.markdown(f"🪙 **Drop Mesas:** {formatear_monto(drop_mesas)}")
    else:
        st.warning("⚠️ No se encontraron datos para la fecha seleccionada.")

        # Debug opcional (si quieres ver qué fechas hay realmente)
        # st.write("Rango de fechas:", df["Fecha"].min(), df["Fecha"].max())
        # st.write("Ejemplos:", df["Fecha"].dropna().head(10))

except FileNotFoundError:
    st.error("❌ El archivo 'CIERRE_PPTO_2025.xlsx' no se encontró.")
except Exception as e:
    st.error(f"❌ Error: {e}")
