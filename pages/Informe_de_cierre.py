import base64
import io
import os
import textwrap
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageFont

FILE_PATH = "CIERRE_PPTO_2025.xlsx"
SHEET_NAME = "bases"


def jornada_actual():
    ahora = datetime.now(ZoneInfo("America/Santiago"))
    return (ahora - timedelta(days=1)).date() if ahora.hour < 8 else ahora.date()


def entero(valor):
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return 0


def pesos(valor):
    return f"${entero(valor):,}".replace(",", ".")


def cargar_presupuestos(fecha):
    valores = {"MDJ Win Ppto": 0, "MDJ Drop Ppto": 0, "TGM Win Ppto": 0, "TGM CI Ppto": 0}
    if not os.path.exists(FILE_PATH):
        return valores
    df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)
    df.columns = df.iloc[0]
    df = df.iloc[1:].copy()
    df.columns = [str(c).strip() for c in df.columns]
    df.rename(columns={"dia": "Fecha", "WIN TGM": "Win TGM", "COIN IN": "Coin In", "WIN MESAS": "Win Mesas", "DROP": "Drop Mesas"}, inplace=True)
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce", dayfirst=True).dt.date
    filas = df[df["Fecha"] == fecha]
    if filas.empty:
        return valores
    fila = filas.iloc[0]
    return {
        "MDJ Win Ppto": entero(fila.get("Win Mesas")),
        "MDJ Drop Ppto": entero(fila.get("Drop Mesas")),
        "TGM Win Ppto": entero(fila.get("Win TGM")),
        "TGM CI Ppto": entero(fila.get("Coin In")),
    }


def fuente(tamano, negrita=False):
    nombres = ["DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if negrita else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for nombre in nombres:
        try:
            return ImageFont.truetype(nombre, tamano)
        except OSError:
            pass
    return ImageFont.load_default()


def crear_imagen(fecha, resultados, po, pagos, sobre_millon, novedades, jackpots, ingresos):
    ancho, margen = 1200, 34
    filas_novedades = []
    for area, texto in novedades.items():
        lineas = textwrap.wrap(texto.strip() or "Sin novedades", width=88) or ["Sin novedades"]
        filas_novedades.append((area, lineas))
    alto = 610 + sum(max(56, 26 * len(lineas) + 24) for _, lineas in filas_novedades) + 60 * len(jackpots)
    img = Image.new("RGB", (ancho, alto), "#f7f9fc")
    d = ImageDraw.Draw(img)
    f12, f14, f16, f20, f28 = fuente(18), fuente(20), fuente(22, True), fuente(26, True), fuente(36, True)
    azul, tinta, borde = "#1787a8", "#172033", "#aab4c3"
    y = 30
    d.rounded_rectangle((margen, y, ancho-margen, y+82), 18, fill="#10324b")
    d.text((margen+24, y+18), "INFORME DE CIERRE", font=f28, fill="white")
    fecha_txt = fecha.strftime("%d-%m-%Y")
    caja = d.textbbox((0, 0), fecha_txt, font=f20)
    d.text((ancho-margen-24-(caja[2]-caja[0]), y+25), fecha_txt, font=f20, fill="#8fe3f7")
    y += 104

    def titulo(texto):
        nonlocal y
        d.rounded_rectangle((margen, y, ancho-margen, y+42), 8, fill=azul)
        d.text((margen+16, y+8), texto, font=f16, fill="white")
        y += 50

    titulo("RESULTADOS")
    encabezados = ["Ãrea / Indicador", "Presupuesto", "Resultado", "Cumplimiento"]
    xs = [margen, 360, 620, 890, ancho-margen]
    for i, texto in enumerate(encabezados):
        d.rectangle((xs[i], y, xs[i+1], y+42), fill="#dcebf2", outline=borde)
        d.text((xs[i]+10, y+10), texto, font=f14, fill=tinta)
    y += 42
    for nombre, ppto, real in resultados:
        cumplimiento = (real / ppto * 100) if ppto else 0
        fondo = "#dff4e5" if cumplimiento >= 100 else "#ffe0e0"
        textos = [nombre, pesos(ppto), pesos(real), f"{cumplimiento:.1f}%".replace(".", ",")]
        for i, texto in enumerate(textos):
            d.rectangle((xs[i], y, xs[i+1], y+48), fill=fondo if i >= 2 else "white", outline=borde)
            d.text((xs[i]+10, y+12), texto, font=f14, fill="#16733b" if i >= 2 and cumplimiento >= 100 else ("#b42318" if i >= 2 else tinta))
        y += 48
    d.rectangle((margen, y, ancho-margen, y+46), fill="white", outline=borde)
    d.text((margen+12, y+11), f"PO: {po:.1f}%   |   Pagos totales: {pagos}   |   Pagos sobre $1.000.000: {sobre_millon}", font=f14, fill=tinta)
    y += 58

    titulo("NOVEDADES")
    for area, lineas in filas_novedades:
        h = max(56, 26 * len(lineas) + 24)
        d.rectangle((margen, y, margen+190, y+h), fill="#eef3f7", outline=borde)
        d.text((margen+12, y+14), area, font=f16, fill=tinta)
        d.rectangle((margen+190, y, ancho-margen, y+h), fill="white", outline=borde)
        d.multiline_text((margen+206, y+12), "\n".join(lineas), font=f12, fill=tinta, spacing=5)
        y += h
    for monto, tipo, detalle in jackpots:
        if not (monto or detalle.strip()):
            continue
        d.rectangle((margen, y, ancho-margen, y+52), fill="#fff7df", outline=borde)
        d.text((margen+12, y+13), f"TGM Â· {pesos(monto)} Â· {tipo} Â· {detalle.strip()}", font=f14, fill=tinta)
        y += 52
    y += 12

    titulo("INGRESOS")
    etiquetas = [("TOTAL", ingresos[0]), ("CORTESÃAS", ingresos[1]), ("VENTA", ingresos[2])]
    for etiqueta, valor in etiquetas:
        d.rectangle((margen, y, margen+270, y+46), fill="#eef3f7", outline=borde)
        d.rectangle((margen+270, y, ancho-margen, y+46), fill="white", outline=borde)
        d.text((margen+12, y+11), etiqueta, font=f16, fill=tinta)
        d.text((margen+290, y+11), str(valor), font=f14, fill=tinta)
        y += 46
    y += 20
    salida = io.BytesIO()
    img.crop((0, 0, ancho, min(alto, y))).save(salida, format="PNG", optimize=True)
    return salida.getvalue()


st.set_page_config(page_title="Informe de cierre", page_icon="ðŸ“", layout="centered")
st.markdown("<style>.block-container{max-width:850px;padding-top:1rem} div[data-testid='stNumberInput'] input{text-align:right}</style>", unsafe_allow_html=True)
st.page_link("consulta_montos_streamlit.py", label="â† Volver a consulta de presupuesto")
st.title("ðŸ“ Informe de cierre")
st.caption("Completa los datos y genera una imagen lista para enviar.")

fecha = st.date_input("Fecha de jornada", value=jornada_actual(), format="DD/MM/YYYY")
presupuestos = cargar_presupuestos(fecha)
if not any(presupuestos.values()):
    st.info("No se encontraron presupuestos para esta fecha. Puedes ingresarlos manualmente.")

st.subheader("Resultados")
resultados = []
for nombre in presupuestos:
    c1, c2 = st.columns(2)
    with c1:
        ppto = st.number_input(nombre, min_value=0, value=presupuestos[nombre], step=1000, key=f"p_{nombre}")
    with c2:
        real = st.number_input("Resultado", value=0, step=1000, key=f"r_{nombre}")
    resultados.append((nombre, ppto, real))
c1, c2, c3 = st.columns(3)
po = c1.number_input("PO (%)", value=0.0, step=0.1)
pagos = c2.text_input("Pagos totales", placeholder="Ej.: 8 x $4.258.905")
sobre_millon = c3.number_input("Pagos sobre millÃ³n", min_value=0, value=0, step=1)

st.subheader("Novedades")
areas = ["MDJ", "EC / TGM", "TO", "SEGURIDAD", "MANTENCIÃ“N", "TIC", "BAR / COCINA"]
novedades = {area: st.text_area(area, value="Sin novedades", height=70, key=f"n_{area}") for area in areas}

with st.expander("Jackpots TGM (opcional)"):
    jackpots = []
    for i in range(3):
        c1, c2, c3 = st.columns([1, 1, 2])
        monto = c1.number_input("Monto", min_value=0, value=0, step=1000, key=f"jm_{i}")
        tipo = c2.text_input("Tipo", value="Jackpot", key=f"jt_{i}")
        detalle = c3.text_input("Cliente / CategorÃ­a / TGM", key=f"jd_{i}")
        jackpots.append((monto, tipo, detalle))

st.subheader("Ingresos")
c1, c2, c3 = st.columns(3)
total = c1.number_input("Total", min_value=0, value=0, step=1)
cortesias = c2.number_input("CortesÃ­as", min_value=0, value=0, step=1)
venta = c3.number_input("Venta", min_value=0, value=0, step=1)

if st.button("Generar informe", type="primary", use_container_width=True):
    st.session_state["informe_png"] = crear_imagen(fecha, resultados, po, pagos, sobre_millon, novedades, jackpots, (total, cortesias, venta))

if "informe_png" in st.session_state:
    png = st.session_state["informe_png"]
    st.divider()
    st.subheader("Vista previa")
    st.image(png, use_container_width=True)
    st.download_button("â¬‡ï¸ Descargar PNG", png, file_name=f"informe_cierre_{fecha:%d-%m-%Y}.png", mime="image/png", use_container_width=True)
    b64 = base64.b64encode(png).decode("ascii")
    components.html(f"""
    <button id="copy" style="width:100%;padding:12px;border:0;border-radius:8px;background:#1787a8;color:white;font:600 16px sans-serif;cursor:pointer">ðŸ“‹ Copiar imagen</button>
    <div id="msg" style="font:14px sans-serif;margin-top:8px;color:#334155"></div>
    <script>
    document.getElementById('copy').onclick = async () => {{
      const msg = document.getElementById('msg');
      try {{
        const blob = await (await fetch('data:image/png;base64,{b64}')).blob();
        await navigator.clipboard.write([new ClipboardItem({{'image/png': blob}})]);
        msg.textContent = 'Imagen copiada. Ya puedes pegarla en WhatsApp o correo.';
      }} catch (e) {{ msg.textContent = 'El navegador bloqueÃ³ la copia. Usa Descargar PNG.'; }}
    }};
    </script>""", height=72)

