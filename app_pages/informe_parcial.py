import base64
import io
import os
import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import pytesseract
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageFont, ImageOps

FILE_PATH = "CIERRE_PPTO_2025.xlsx"
SHEET_NAME = "bases"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MONEDA_COMPONENT = st.components.v2.component(
    "campo_moneda_parcial_clp",
    html='''<label class="clp-label"></label><input class="clp-input" inputmode="numeric" autocomplete="off" />''',
    css='''
    :host { display:block; font-family:var(--st-font); }
    .clp-label { display:block; color:var(--st-text-color); font-size:0.875rem; font-weight:600; margin-bottom:0.35rem; }
    .clp-input { width:100%; box-sizing:border-box; min-height:2.5rem; padding:0.55rem 0.75rem; border:1px solid rgba(128,128,128,.35); border-radius:0.5rem; background:var(--st-secondary-background-color); color:var(--st-text-color); font:inherit; text-align:right; }
    .clp-input:focus { outline:2px solid var(--st-primary-color); border-color:transparent; }
    ''',
    js='''
    export default function(component) {
      const { parentElement, data, setStateValue } = component;
      const label = parentElement.querySelector('.clp-label');
      const input = parentElement.querySelector('.clp-input');
      label.textContent = data.label;
      const format = (raw) => {
        const negative = String(raw || '').trim().startsWith('-');
        const digits = String(raw || '').replace(/[^0-9]/g, '');
        if (!digits) return negative ? '-' : '';
        return (negative ? '-$' : '$') + Number(digits).toLocaleString('es-CL');
      };
      if (document.activeElement !== input && input.value !== data.value) {
        input.value = data.value || '';
      }
      input.onfocus = () => input.select();
      input.oninput = () => {
        input.value = format(input.value);
        input.setSelectionRange(input.value.length, input.value.length);
      };
      const commit = () => setStateValue('value', input.value);
      input.onblur = commit;
      input.onkeydown = (event) => {
        if (event.key === '-' && !input.value.startsWith('-')) {
          event.preventDefault();
          input.value = input.value ? '-' + input.value.replace('-', '') : '-';
          input.setSelectionRange(input.value.length, input.value.length);
        } else if (event.key === 'Enter') {
          event.preventDefault();
          commit();
          input.blur();
        }
      };
    }
    ''',
)


def jornada_actual():
    ahora = datetime.now(ZoneInfo("America/Santiago"))
    return (ahora - timedelta(days=1)).date() if ahora.hour < 8 else ahora.date()


def entero(valor):
    if isinstance(valor, str):
        negativo = valor.strip().startswith("-")
        numero = int("".join(c for c in valor if c.isdigit()) or 0)
        return -numero if negativo else numero
    try:
        return int(valor)
    except (TypeError, ValueError):
        return 0


def pesos(valor):
    numero = entero(valor)
    signo = "-" if numero < 0 else ""
    return f"{signo}${abs(numero):,}".replace(",", ".")


def campo_monto(etiqueta, clave):
    estado = st.session_state.get(clave, {})
    actual = estado.get("value", "") if isinstance(estado, dict) else ""
    resultado = MONEDA_COMPONENT(
        data={"label": etiqueta, "value": actual},
        default={"value": actual},
        key=clave,
        on_value_change=lambda: None,
    )
    return entero(resultado.value if resultado.value is not None else actual)


def campo_entero(etiqueta, clave):
    if clave not in st.session_state:
        st.session_state[clave] = ""

    def normalizar():
        st.session_state[clave] = str(entero(st.session_state[clave]))

    return entero(st.text_input(etiqueta, key=clave, on_change=normalizar, placeholder="0"))


def recortes_ocr(imagen, tipo):
    imagen = ImageOps.exif_transpose(imagen).convert("RGB")
    ancho, alto = imagen.size
    if tipo == "coin":
        limites = [(0, .22, .68, 1), (0, .52, .68, 1), (0, 0, 1, 1)]
    elif tipo == "win":
        limites = [(.28, .22, .89, 1), (.28, .52, .89, 1), (0, 0, 1, 1)]
    else:
        limites = [(.70, .20, 1, 1), (.70, .50, 1, 1), (0, 0, 1, 1)]
    for x1, y1, x2, y2 in limites:
        recorte = imagen.crop((int(ancho*x1), int(alto*y1), int(ancho*x2), int(alto*y2)))
        escala = max(3, min(6, 1800 // max(1, recorte.width)))
        recorte = recorte.resize((recorte.width*escala, recorte.height*escala))
        gris = ImageOps.autocontrast(recorte.convert("L"))
        yield gris
        yield gris.point(lambda p: 255 if p > 145 else 0)
        yield gris.point(lambda p: 255 if p > 180 else 0)


def convertir_numero(bruto):
    negativo = "-" in bruto
    limpio = bruto.replace("$", "").replace("-", "").replace(".", "")
    if "," in limpio:
        parte_entera, decimales = limpio.rsplit(",", 1)
        numero = Decimal(f"{parte_entera or '0'}.{decimales or '0'}")
    else:
        numero = Decimal(limpio.replace(",", "") or "0")
    numero = int(numero.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -numero if negativo else numero


def clasificar_captura(archivo):
    imagen = ImageOps.exif_transpose(Image.open(archivo)).convert("RGB")
    escala = max(1, min(4, 1800 // max(1, imagen.width)))
    imagen = imagen.resize((imagen.width*escala, imagen.height*escala))
    gris = ImageOps.autocontrast(imagen.convert("L"))
    textos = [pytesseract.image_to_string(gris, config=f"--psm {psm}") for psm in (6, 11)]
    texto = "\n".join(textos)
    normalizado = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    compacto = re.sub(r"[^a-z0-9]", "", normalizado)
    if "jugado" in compacto or "jvgado" in compacto:
        return "coin", texto
    if "netwin" in compacto or "netwim" in compacto or "netvin" in compacto:
        return "win", texto
    if "total" in compacto and any(palabra in compacto for palabra in ("corte", "document", "hasta")):
        return "ingresos", texto
    raise ValueError("No se identificó si corresponde a Jugado, Netwin o Total de Boletería")


def extraer_ultimo_numero(archivo, tipo):
    imagen = Image.open(archivo)
    candidatos, textos = [], []
    for preparada in recortes_ocr(imagen, tipo):
        for psm in (6, 11):
            datos = pytesseract.image_to_data(
                preparada,
                config=f"--psm {psm} -c tessedit_char_whitelist=0123456789$.,-",
                output_type=pytesseract.Output.DICT,
            )
            lineas = {}
            for i, token in enumerate(datos["text"]):
                token = token.strip()
                if not token:
                    continue
                clave = (datos["block_num"][i], datos["par_num"][i], datos["line_num"][i])
                linea = lineas.setdefault(clave, {"tokens": [], "top": datos["top"][i]})
                linea["tokens"].append(token)
                linea["top"] = max(linea["top"], datos["top"][i])
            for linea in lineas.values():
                texto = "".join(linea["tokens"]).replace("—", "-")
                textos.append(texto)
                for bruto in re.findall(r"-?\$?-?\d[\d.,-]*", texto):
                    bruto = bruto.rstrip(".,-")
                    digitos = sum(ch.isdigit() for ch in bruto)
                    if digitos >= (2 if tipo == "ingresos" else 4):
                        posicion = linea["top"] / max(1, preparada.height)
                        candidatos.append((bruto, digitos, posicion))
    if not candidatos:
        raise ValueError("No se detectó un número")
    if tipo == "ingresos":
        bruto = max(candidatos, key=lambda x: (x[2], -abs(x[1]-3)))[0]
    else:
        bruto = max(candidatos, key=lambda x: (x[1], x[2]))[0]
    return convertir_numero(bruto), "\n".join(dict.fromkeys(textos))


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


def crear_imagen(fecha, ppto, win, coin, ingresos):
    avance = win / ppto * 100 if ppto else 0
    estado, color, fondo = estado_avance(avance)
    ancho, alto, margen = 900, 360, 26
    img = Image.new("RGB", (ancho, alto), "#f7f9fc")
    d = ImageDraw.Draw(img)
    f14, f18, f24, f34 = fuente(18), fuente(22, True), fuente(28, True), fuente(38, True)
    d.rounded_rectangle((margen, 22, ancho-margen, 82), 14, fill="#10324b")
    titulo = f"INFORME PARCIAL | {fecha:%d-%m-%Y}"
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

fecha = st.date_input("Fecha de jornada", value=jornada_actual(), format="DD/MM/YYYY")
ppto = presupuesto_win(fecha)
st.metric("PPTO Win TGM del día", pesos(ppto))

with st.expander("📷 Leer capturas o fotos", expanded=True):
    st.caption("Selecciona o arrastra juntas las imágenes de Jugado, Netwin y Boletería.")
    capturas = st.file_uploader(
        "Capturas o fotos",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="ocr_capturas",
    )
    if st.button("Leer capturas", use_container_width=True):
        detectados, detalles, errores, asignaciones = {}, {}, [], []
        for archivo in capturas:
            try:
                tipo, texto_clasificacion = clasificar_captura(archivo)
                archivo.seek(0)
                detectados[tipo], detalles[tipo] = extraer_ultimo_numero(archivo, tipo)
                detalles[f"clasificación {archivo.name}"] = texto_clasificacion
                nombre_tipo = {"coin": "Coin In", "win": "Win", "ingresos": "Ingresos"}[tipo]
                asignaciones.append(f"{archivo.name} → {nombre_tipo}")
            except Exception as error:
                errores.append(f"{archivo.name}: {error}")
        if "coin" in detectados:
            st.session_state[f"parcial_coin_{fecha}"] = {"value": pesos(detectados["coin"])}
        if "win" in detectados:
            st.session_state[f"parcial_win_{fecha}"] = {"value": pesos(detectados["win"])}
        if "ingresos" in detectados:
            st.session_state[f"parcial_ingresos_{fecha}"] = str(max(0, detectados["ingresos"]))
        st.session_state["ocr_resultado"] = (detectados, errores, detalles, asignaciones)
        st.rerun()
    if "ocr_resultado" in st.session_state:
        resultado_guardado = st.session_state["ocr_resultado"]
        if len(resultado_guardado) == 3:
            detectados, errores, detalles = resultado_guardado
            asignaciones = []
        else:
            detectados, errores, detalles, asignaciones = resultado_guardado
        if asignaciones:
            st.info("Clasificación · " + " | ".join(asignaciones))
        if detectados:
            partes = []
            if "coin" in detectados: partes.append(f"Coin In: {pesos(detectados['coin'])}")
            if "win" in detectados: partes.append(f"Win: {pesos(detectados['win'])}")
            if "ingresos" in detectados: partes.append(f"Ingresos: {detectados['ingresos']}")
            st.success("Detectado · " + " | ".join(partes))
        if errores:
            st.warning("No se pudo leer: " + " | ".join(errores))
        with st.expander("Ver texto reconocido"):
            st.code("\n".join(f"{k}: {v}" for k, v in detalles.items()) or "Sin texto")

c1, c2, c3 = st.columns([1, 1, .7])
with c1:
    win = campo_monto("Win acumulado", f"parcial_win_{fecha}")
with c2:
    coin = campo_monto("Coin In acumulado", f"parcial_coin_{fecha}")
with c3:
    ingresos = campo_entero("Ingresos", f"parcial_ingresos_{fecha}")

avance = win / ppto * 100 if ppto else 0
estado, _, _ = estado_avance(avance)
st.metric("Avance PPTO diario", f"{avance:.1f}%".replace(".", ","), estado)

if st.button("Generar informe parcial", type="primary", use_container_width=True):
    st.session_state["parcial_png"] = crear_imagen(fecha, ppto, win, coin, ingresos)

if "parcial_png" in st.session_state:
    png = st.session_state["parcial_png"]
    st.image(png, use_container_width=True)
    st.download_button("Descargar PNG", png, file_name=f"informe_parcial_{fecha:%d-%m-%Y}.png", mime="image/png", use_container_width=True)
    b64 = base64.b64encode(png).decode("ascii")
    components.html(f'''<button id="copy" style="width:100%;padding:12px;border:0;border-radius:8px;background:#1787a8;color:white;font:600 16px sans-serif">Copiar imagen</button><div id="msg"></div><script>document.getElementById('copy').onclick=async()=>{{try{{const blob=await(await fetch('data:image/png;base64,{b64}')).blob();await navigator.clipboard.write([new ClipboardItem({{'image/png':blob}})]);document.getElementById('msg').textContent='Imagen copiada.'}}catch(e){{document.getElementById('msg').textContent='Usa Descargar PNG.'}}}}</script>''', height=68)

