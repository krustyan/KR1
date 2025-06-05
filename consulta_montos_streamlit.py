
import streamlit as st
import pandas as pd
import locale

# Configurar formato CLP
locale.setlocale(locale.LC_ALL, 'es_CL.UTF-8')

@st.cache_data
def load_data():
    xls = pd.ExcelFile("CIERRE_PPTO_2025.xlsx")
    df = pd.read_excel(xls, sheet_name="bases")

    headers = df.iloc[0].tolist()
    df = df.iloc[1:].copy()
    df.columns = [str(h).strip() for h in headers]
    df.columns = [c.strip() for c in df.columns]

    # Renombrar columnas según nombres exactos del Excel
    df.rename(columns={
        "WIN TGM": "Win TGM",
        "COIN IN": "CI TGM",
        "WIN MESAS": "Win Mesas",
        "DROP": "DROP Mesas"
    }, inplace=True)

    df.rename(columns={df.columns[0]: "fecha"}, inplace=True)
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["día_semana"] = df["fecha"].dt.day_name(locale="es_CL.utf8")
    df["Fecha"] = df["fecha"].dt.strftime('%d/%m/%Y')  # formato día/mes/año

    # Limpiar símbolos monetarios
    for col in ["Win TGM", "CI TGM", "Win Mesas", "DROP Mesas"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace("[$,]", "", regex=True)
                .astype(float)
                .fillna(0)
            )
        else:
            df[col] = pd.Series([0]*len(df))

    return df

def get_val(df, col):
    try:
        return int(float(df.loc[df.index[0], col]))
    except:
        return 0

df_bases = load_data()

st.markdown("<h1 style='text-align: center;'>📊 Presupuesto Diario Casino Enjoy Los Ángeles</h1>", unsafe_allow_html=True)

fecha_input = st.date_input("Selecciona una fecha")
resultado = df_bases[df_bases["fecha"] == pd.to_datetime(fecha_input)]

if not resultado.empty:
    win_tgm = get_val(resultado, "Win TGM")
    ci_tgm = get_val(resultado, "CI TGM")
    win_mesas = get_val(resultado, "Win Mesas")
    drop_mesas = get_val(resultado, "DROP Mesas")

    dia_semana = resultado["día_semana"].iloc[0]
    fecha_limpia = resultado["Fecha"].iloc[0]

    st.markdown("---")
    st.markdown(f"### 📅 {dia_semana} - {fecha_limpia}")
    st.markdown(f"### 🎰 Win TGM: `{locale.currency(win_tgm, grouping=True)}`")
    st.markdown(f"### 💰 CI TGM: `{locale.currency(ci_tgm, grouping=True)}`")
    st.markdown(f"### 🎲 Win Mesas: `{locale.currency(win_mesas, grouping=True)}`")
    st.markdown(f"### 📉 DROP Mesas: `{locale.currency(drop_mesas, grouping=True)}`")
    st.markdown("---")
else:
    st.warning("⚠️ No se encontraron datos para la fecha seleccionada.")
