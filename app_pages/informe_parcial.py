import base64
import io
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageFont

FILE_PATH = "CIERRE_PPTO_2025.xlsx"
SHEET_NAME = "bases"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def jornada_actual():
    ahora = datetime.now(ZoneInfo("America/Santiago"))
    return (ahora - timedelta(days=1)).date() if ahora.hour < 8 else ahora.date()


def entero(valor):
    if isinstance(valor, str):
        return int("".join(c for c in valor if c.isdigit()) or 0)
    try:
        return int(valor)
    except (TypeError, ValueError):
        return 0


def pesos(valor):
    return f"${entero(valor):,}".replace(",", ".")


def campo_monto(etiqueta, clave):
    if clave not in st.session_state:
        st.session_state[clave] = ""

    def formato():
        st.session_state[clave] = pesos(st.session_state[clave])

    return entero(st.text_input(etiqueta, key=clave, on_change=formato, placeholder="$0"))


@st.cache_data
def presupuesto_win(fecha):
    if not os.path.exists(FILE_PATH):
        return 0
    df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)
    df.columns = df.iloc[0]
    df = df.iloc[1:].copy()
    df.columns = [str(c).strip() for c in df.columns]
    df.rename(columns={"dia": "Fecha", "WIN TGM": "Win TGM"}, inplace=True)
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce", dayfirst=True).dt.date
    fila = df[df["Fecha"] == fecha]
    return entero(fila.iloc[0].get("Win TGM")) if not fila.empty else 0


def fuente(tamano, negrita=False):
    archivo = "Ubuntu-B.ttf" if negrita else "Ubuntu-R.ttf"
    for ruta in [os.path.join(BASE_DIR, "assets", archivo), archivo]:
        try:
            return ImageFont.truetype(ruta, tamano)
        except OSError:
            pass
    return ImageFont.load_default()


def estado_avance(avance):
    if avance >= 100:
        return "META CUMPLIDA", "#16733b", "#dff4e5"
    if avance >= 50:
        return "AVANCE", "#9a6700", "#fff2c7"
    return "EN DESARROLLO", "#1769aa", "#dceeff"


def crear_imagen(fecha, hora, ppto, win, coin, ingresos):
    avance = win / ppto * 100 if ppto else 0
    estado, color, fondo = estado_avance(avance)
    ancho, alto, margen = 900, 360, 26
    img = Image.new("RGB", (ancho, alto), "#f7f9fc")
    d = ImageDraw.Draw(img)
    f14, f18, f24, f34 = fuente(18), fuente(22, True), fuente(28, True), fuente(38, True)
    d.rounded_rectangle((margen, 22, ancho-margen, 82), 14, fill="#10324b")
    titulo = f"INFORME PARCIAL | {fecha:%d-%m-%Y} | {hora}"
    caja = d.textbbox((0, 0), titulo, font=f34)
    d.text(((ancho-(caja[2]-caja[0]))/2, 31), titulo, font=f34, fill="white")
    d.rounded_rectangle((margen, 96, ancho-margen, 143), 10, fill=fondo, outline=color, width=2)
    d.text((margen+18, 107), estado, font=f24, fill=color)
    avance_txt = f"AVANCE PPTO DIARIO: {avance:.1f}%".replace(".", ",")
    caja = d.textbbox((0, 0), avance_txt, font=f24)
    d.text((ancho-margen-18-(caja[2]-caja[0]), 107), avance_txt, font=f24, fill=color)
    datos = [
        ("PPTO WIN DÍA", pesos(ppto)),
        ("WIN ACUMULADO", pesos(win)),
        ("COIN IN ACUMULADO", pesos(coin)),
        ("INGRESOS", str(ingresos)),
    ]
    y = 158
    col = (ancho - 2*margen) // 2
    for i, (etiqueta, valor) in enumerate(datos):
        fila, columna = divmod(i, 2)
        x1, y1 = margen + columna*col, y + fila*82
        x2 = ancho-margen if columna == 1 else x1+col
        d.rounded_rectangle((x1, y1, x2-8, y1+70), 9, fill="white", outline="#bcc7d3")
        d.text((x1+14, y1+9), etiqueta, font=f14, fill="#526071")
        d.text((x1+14, y1+32), valor, font=f18, fill="#172033")
    salida = io.BytesIO()
    img.save(salida, "PNG", optimize=True)
    return salida.getvalue()


st.set_page_config(page_title="Informe parcial", page_icon="⏱️", layout="centered")
st.markdown("<style>.block-container{max-width:760px;padding-top:1rem}</style>", unsafe_allow_html=True)
st.title("⏱️ Informe parcial")
st.caption("Avance acumulado respecto del presupuesto total de la jornada.")

c1, c2 = st.columns(2)
fecha = c1.date_input("Fecha de jornada", value=jornada_actual(), format="DD/MM/YYYY")
hora = c2.time_input("Hora del corte", value=datetime.now(ZoneInfo("America/Santiago")).time().replace(second=0, microsecond=0)).strftime("%H:%M")
ppto = presupuesto_win(fecha)
st.metric("PPTO Win TGM del día", pesos(ppto))

c1, c2, c3 = st.columns([1, 1, .7])
with c1:
    win = campo_monto("Win acumulado", f"parcial_win_{fecha}")
with c2:
    coin = campo_monto("Coin In acumulado", f"parcial_coin_{fecha}")
with c3:
    ingresos = st.number_input("Ingresos", min_value=0, value=0, step=1)

avance = win / ppto * 100 if ppto else 0
estado, _, _ = estado_avance(avance)
st.metric("Avance PPTO diario", f"{avance:.1f}%".replace(".", ","), estado)

if st.button("Generar informe parcial", type="primary", use_container_width=True):
    st.session_state["parcial_png"] = crear_imagen(fecha, hora, ppto, win, coin, ingresos)

if "parcial_png" in st.session_state:
    png = st.session_state["parcial_png"]
    st.image(png, use_container_width=True)
    st.download_button("Descargar PNG", png, file_name=f"informe_parcial_{fecha:%d-%m-%Y}_{hora.replace(':','-')}.png", mime="image/png", use_container_width=True)
    b64 = base64.b64encode(png).decode("ascii")
    components.html(f'''<button id="copy" style="width:100%;padding:12px;border:0;border-radius:8px;background:#1787a8;color:white;font:600 16px sans-serif">Copiar imagen</button><div id="msg"></div><script>document.getElementById('copy').onclick=async()=>{{try{{const blob=await(await fetch('data:image/png;base64,{b64}')).blob();await navigator.clipboard.write([new ClipboardItem({{'image/png':blob}})]);document.getElementById('msg').textContent='Imagen copiada.'}}catch(e){{document.getElementById('msg').textContent='Usa Descargar PNG.'}}}}</script>''', height=68)

