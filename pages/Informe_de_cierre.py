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
MAQUINAS_PATH = "data/maquinas.tsv"
CATEGORIAS = ["Silver", "Gold", "Platinum", "Diamond", "Seven Star"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MONEDA_COMPONENT = st.components.v2.component(
    "campo_moneda_clp",
    html='''<label class="clp-label"></label><input class="clp-input" inputmode="numeric" autocomplete="off" />''',
    css='''
    :host { display:block; font-family:var(--st-font); }
    .clp-label { display:block; color:var(--st-text-color); font-size:0.875rem; font-weight:600; margin-bottom:0.35rem; }
    .clp-input { width:100%; box-sizing:border-box; min-height:2.5rem; padding:0.55rem 0.75rem; border:1px solid rgba(128,128,128,.35); border-radius:0.5rem; background:var(--st-secondary-background-color); color:var(--st-text-color); font:inherit; text-align:right; }
    .clp-input:focus { outline:2px solid var(--st-primary-color); border-color:transparent; }
    .clp-input:disabled { opacity:.65; cursor:not-allowed; }
    ''',
    js='''
    export default function({ parentElement, data, setStateValue }) {
      const label = parentElement.querySelector('.clp-label');
      const input = parentElement.querySelector('.clp-input');
      label.textContent = data.label;
      input.disabled = Boolean(data.disabled);
      const format = (raw) => {
        const negative = String(raw ?? '').trim().startsWith('-');
        const digits = String(raw ?? '').replace(/\\D/g, '');
        if (!digits) return negative ? '-' : '';
        return (negative ? '-$' : '$') + Number(digits).toLocaleString('es-CL');
      };
      if (document.activeElement !== input && input.value !== data.value) input.value = data.value ?? '';
      input.onfocus = () => { if (!input.disabled) input.select(); };
      input.oninput = () => {
        input.value = format(input.value);
        input.setSelectionRange(input.value.length, input.value.length);
      };
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
      const commit = () => setStateValue('value', input.value);
      input.onblur = commit;
    }
    ''',
)


def jornada_actual():
    ahora = datetime.now(ZoneInfo("America/Santiago"))
    return (ahora - timedelta(days=1)).date() if ahora.hour < 8 else ahora.date()


def entero(valor):
    if isinstance(valor, str):
        negativo = valor.strip().startswith("-")
        digitos = "".join(c for c in valor if c.isdigit())
        return (-1 if negativo else 1) * int(digitos or 0)
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return 0


def pesos(valor):
    numero = entero(valor)
    signo = "-" if numero < 0 else ""
    return f"{signo}${abs(numero):,}".replace(",", ".")


def campo_monto(etiqueta, valor, clave, deshabilitado=False):
    inicial = pesos(valor) if valor or deshabilitado else ""
    estado = st.session_state.get(clave, {})
    actual = estado.get("value", inicial) if isinstance(estado, dict) else inicial
    resultado = MONEDA_COMPONENT(
        data={"label": etiqueta, "value": actual, "disabled": deshabilitado},
        default={"value": actual},
        key=clave,
        on_value_change=lambda: None,
    )
    return entero(resultado.value if resultado.value is not None else actual)


def campo_entero(etiqueta, valor, clave):
    if clave not in st.session_state:
        st.session_state[clave] = str(valor) if valor else ""

    def normalizar():
        st.session_state[clave] = str(max(0, entero(st.session_state[clave])))

    texto = st.text_input(etiqueta, key=clave, on_change=normalizar, placeholder="0")
    return max(0, entero(texto))


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


@st.cache_data
def cargar_maquinas():
    if not os.path.exists(MAQUINAS_PATH):
        return {}
    df = pd.read_csv(MAQUINAS_PATH, sep="\t", dtype=str, names=["maquina", "salon", "banco"])
    return {fila.maquina: (fila.salon, fila.banco) for fila in df.itertuples(index=False)}


def fuente(tamano, negrita=False):
    nombres = [
        os.path.join(BASE_DIR, "assets", "Ubuntu-B.ttf" if negrita else "Ubuntu-R.ttf"),
        "Ubuntu-B.ttf" if negrita else "Ubuntu-R.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf" if negrita else "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf",
    ]
    for nombre in nombres:
        try:
            return ImageFont.truetype(nombre, tamano)
        except OSError:
            pass
    return ImageFont.load_default()


def crear_imagen(fecha, resultados, po, cantidad_pagos, monto_pagos, sobre_millon, novedades, jackpots, ingresos):
    ancho, margen = 900, 22
    filas_novedades = []
    areas_sin_novedad = []
    for area, texto in novedades.items():
        limpio = texto.strip() or "Sin novedades"
        if limpio.casefold() == "sin novedades":
            areas_sin_novedad.append(area)
        else:
            filas_novedades.append((area, textwrap.wrap(limpio, width=58) or [limpio]))
    alto = 520 + sum(max(32, 18 * len(lineas) + 12) for _, lineas in filas_novedades) + 34 * len(jackpots)
    img = Image.new("RGB", (ancho, alto), "#f7f9fc")
    d = ImageDraw.Draw(img)
    f12, f14, f16, f20, f28 = fuente(15), fuente(17), fuente(19, True), fuente(22, True), fuente(36, True)
    azul, tinta, borde = "#1787a8", "#172033", "#aab4c3"
    y = 20
    d.rounded_rectangle((margen, y, ancho-margen, y+54), 14, fill="#10324b")
    encabezado = f"INFORME DE CIERRE | {fecha:%d-%m-%Y}"
    tamano_titulo = 36
    fuente_titulo = f28
    while d.textbbox((0, 0), encabezado, font=fuente_titulo)[2] > ancho - (2 * margen) - 36 and tamano_titulo > 24:
        tamano_titulo -= 1
        fuente_titulo = fuente(tamano_titulo, True)
    caja = d.textbbox((0, 0), encabezado, font=fuente_titulo)
    x_titulo = (ancho - (caja[2] - caja[0])) // 2
    d.text((x_titulo, y+8), encabezado, font=fuente_titulo, fill="white")
    y += 66

    def titulo(texto):
        nonlocal y
        d.rounded_rectangle((margen, y, ancho-margen, y+27), 7, fill=azul)
        d.text((margen+14, y+5), texto, font=f16, fill="white")
        y += 33

    titulo("RESULTADOS")
    encabezados = ["Área / Indicador", "Presupuesto", "Resultado", "Cumplimiento"]
    xs = [margen, 245, 455, 665, ancho-margen]
    for i, texto in enumerate(encabezados):
        d.rectangle((xs[i], y, xs[i+1], y+27), fill="#dcebf2", outline=borde)
        d.text((xs[i]+8, y+7), texto, font=f12, fill=tinta)
    y += 27
    for nombre, ppto, real in resultados:
        cumplimiento = (real / ppto * 100) if ppto else 0
        fondo = "#dff4e5" if cumplimiento >= 100 else "#ffe0e0"
        textos = [nombre, pesos(ppto), pesos(real), f"{cumplimiento:.1f}%".replace(".", ",")]
        for i, texto in enumerate(textos):
            d.rectangle((xs[i], y, xs[i+1], y+31), fill=fondo if i >= 2 else "white", outline=borde)
            d.text((xs[i]+8, y+8), texto, font=f12, fill="#16733b" if i >= 2 and cumplimiento >= 100 else ("#b42318" if i >= 2 else tinta))
        y += 31
    resumenes = [
        ("PO JORNADA", f"{po:.2f}%".replace(".", ",")),
        ("CANTIDAD PREMIOS", str(cantidad_pagos)),
        ("MONTO TOTAL PREMIOS", pesos(monto_pagos)),
        ("PREMIOS +$1M", str(sobre_millon)),
    ]
    ancho_resumen = (ancho - 2 * margen) // len(resumenes)
    for i, (etiqueta, valor) in enumerate(resumenes):
        x1 = margen + i * ancho_resumen
        x2 = ancho - margen if i == len(resumenes) - 1 else x1 + ancho_resumen
        d.rectangle((x1, y, x2, y+43), fill="white", outline=borde)
        d.text((x1+7, y+4), etiqueta, font=fuente(12, True), fill="#526071")
        d.text((x1+7, y+20), valor, font=fuente(17, True), fill=tinta)
    y += 51

    if jackpots:
        titulo("JACKPOTS TGM")
        for monto, maquina, salon, categoria, cliente in jackpots:
            d.rectangle((margen, y, ancho-margen, y+31), fill="#fff7df", outline=borde)
            cliente_txt = cliente.strip() or "Cliente sin identificar"
            detalle = f"{pesos(monto)} | {cliente_txt} | {categoria} | Máquina {maquina} | {salon}"
            tamano_detalle = 15
            fuente_detalle = fuente(tamano_detalle, True)
            disponible = ancho - (2 * margen) - 20
            while d.textbbox((0, 0), detalle, font=fuente_detalle)[2] > disponible and tamano_detalle > 12:
                tamano_detalle -= 1
                fuente_detalle = fuente(tamano_detalle, True)
            d.text((margen+10, y+8), detalle, font=fuente_detalle, fill=tinta)
            y += 31
        y += 8

    titulo("NOVEDADES")
    for area, lineas in filas_novedades:
        h = max(34, 18 * len(lineas) + 13)
        d.rectangle((margen, y, margen+240, y+h), fill="#eef3f7", outline=borde)
        d.text((margen+10, y+6), area, font=fuente(13, True), fill=tinta)
        d.rectangle((margen+240, y, ancho-margen, y+h), fill="white", outline=borde)
        d.multiline_text((margen+252, y+8), "\n".join(lineas), font=f12, fill=tinta, spacing=4)
        y += h
    if areas_sin_novedad:
        etiqueta = "TODAS LAS ÁREAS" if not filas_novedades else "SIN NOVEDADES"
        detalle = "Sin novedades" if not filas_novedades else " · ".join(areas_sin_novedad)
        d.rectangle((margen, y, margen+240, y+33), fill="#eef3f7", outline=borde)
        d.rectangle((margen+240, y, ancho-margen, y+33), fill="white", outline=borde)
        d.text((margen+10, y+5), etiqueta, font=fuente(13, True), fill=tinta)
        d.text((margen+252, y+7), detalle, font=f12, fill=tinta)
        y += 33
    y += 8

    titulo("INGRESOS")
    etiquetas = [("TOTAL", ingresos[0]), ("CORTESÍAS", ingresos[1]), ("VENTA", ingresos[2])]
    ancho_col = (ancho - 2 * margen) // 3
    for i, (etiqueta, valor) in enumerate(etiquetas):
        x1 = margen + i * ancho_col
        x2 = ancho - margen if i == 2 else x1 + ancho_col
        d.rectangle((x1, y, x2, y+40), fill="white", outline=borde)
        d.text((x1+10, y+5), etiqueta, font=f12, fill="#526071")
        d.text((x1+10, y+19), str(valor), font=f16, fill=tinta)
    y += 50
    salida = io.BytesIO()
    img.crop((0, 0, ancho, min(alto, y))).save(salida, format="PNG", optimize=True)
    return salida.getvalue()


st.set_page_config(page_title="Informe de cierre", page_icon="📝", layout="centered")
st.markdown("""<style>
.block-container{max-width:850px;padding-top:1rem}
div[data-testid='stTextInput'] input{text-align:right;font-variant-numeric:tabular-nums}
div[data-testid='stNumberInput'] input{text-align:right}
@media (max-width:640px){
  .block-container{padding:0.65rem 0.65rem 2rem}
  div[data-testid='stHorizontalBlock']{gap:0.55rem}
  div[data-testid='stHorizontalBlock']>div{min-width:min(100%,220px)}
  h1{font-size:1.65rem!important}
  h2,h3{font-size:1.2rem!important}
}
</style>""", unsafe_allow_html=True)
st.page_link("app_pages/consulta_ppto.py", label="← Volver a CONSULTA PPTO")
st.title("📝 Informe de cierre")
st.caption("Completa los datos y genera una imagen lista para enviar.")

BORRADOR_KEY = "borrador_informe_cierre"

def limpiar_borrador():
    prefijos = (
        "r_", "jm_", "maq_", "cat_", "cliente_", "cantidad_premios_",
        "pagos_monto_", "sobre_millon_", "ingreso_total_", "ingreso_cortesias_", "n_",
    )
    for clave in list(st.session_state):
        if clave == BORRADOR_KEY or clave == "informe_png" or clave.startswith(prefijos):
            del st.session_state[clave]

if st.button("Limpiar informe", use_container_width=True):
    st.session_state["confirmar_limpieza_cierre"] = True

if st.session_state.get("confirmar_limpieza_cierre"):
    st.warning("¿Seguro que quieres borrar todos los datos del informe?")
    confirmar, cancelar = st.columns(2)
    if confirmar.button("Sí, limpiar", type="primary", use_container_width=True):
        limpiar_borrador()
        st.session_state.pop("confirmar_limpieza_cierre", None)
        st.rerun()
    if cancelar.button("Cancelar", use_container_width=True):
        st.session_state["confirmar_limpieza_cierre"] = False
        st.rerun()

borrador = st.session_state.get(BORRADOR_KEY, {})
for clave, valor in borrador.items():
    if clave not in st.session_state:
        st.session_state[clave] = valor

fecha = st.date_input("Fecha de jornada", value=jornada_actual(), format="DD/MM/YYYY")
presupuestos = cargar_presupuestos(fecha)
if not any(presupuestos.values()):
    st.info("No se encontraron presupuestos para esta fecha. Puedes ingresarlos manualmente.")

st.subheader("Resultados")
resultados = []
for indice, nombre in enumerate(presupuestos):
    c1, c2 = st.columns(2)
    with c1:
        ppto = campo_monto(nombre, presupuestos[nombre], f"p_{fecha}_{indice}", deshabilitado=presupuestos[nombre] != 0)
    with c2:
        real = campo_monto("Resultado", 0, f"r_{fecha}_{indice}")
    resultados.append((nombre, ppto, real))
win_tgm_real = resultados[2][2]
coin_in_real = resultados[3][2]
po = (1 - (win_tgm_real / coin_in_real)) * 100 if coin_in_real else 0.0
c1, c2 = st.columns([1, 2])
c1.metric("PO Jornada", f"{po:.2f}%".replace(".", ","), help="100 × (1 − Win TGM real ÷ Coin In real)")
with c2:
    st.markdown("**Premios de la jornada**")
    p1, p2, p3 = st.columns(3)
    with p1:
        cantidad_pagos = campo_entero("Cantidad de premios", 0, f"cantidad_premios_{fecha}")
    with p2:
        monto_pagos = campo_monto("Monto total de premios", 0, f"pagos_monto_{fecha}")
    with p3:
        sobre_millon = campo_entero("Premios sobre $1M", 0, f"sobre_millon_{fecha}")

jackpots = []
if sobre_millon > 0:
    st.subheader(f"Jackpots TGM ({sobre_millon})")
    st.caption("Completa un registro por cada premio sobre $1.000.000.")
    maquinas = cargar_maquinas()
    if not maquinas:
        st.warning("No se pudo cargar la base de máquinas.")
    for i in range(sobre_millon):
        st.markdown(f"**Jackpot {i + 1}**")
        j1, j2, j3 = st.columns([1, 1, 1])
        with j1:
            monto = campo_monto("Monto", 0, f"jm_{fecha}_{i}")
        maquina = j2.selectbox("Máquina", options=list(maquinas), index=None, placeholder="Escribe o busca…", key=f"maq_{fecha}_{i}")
        categoria = j3.selectbox("Categoría", CATEGORIAS, key=f"cat_{fecha}_{i}")
        salon, _banco = maquinas.get(maquina, ("—", "—"))
        d1, d2 = st.columns([1, 2])
        d1.metric("Salón", salon)
        cliente = d2.text_input("Cliente (opcional)", key=f"cliente_{fecha}_{i}")
        jackpots.append((monto, maquina or "", salon if maquina else "—", categoria, cliente))

st.subheader("Novedades")
areas = ["MDJ", "EC / TGM", "TO", "SEGURIDAD", "MANTENCIÓN", "TIC", "BAR / COCINA"]
novedades = {
    area: st.text_area(area, value="", placeholder="Sin novedades", height=70, key=f"n_{area}")
    for area in areas
}

st.subheader("Ingresos")
c1, c2, c3 = st.columns(3)
with c1:
    total = campo_entero("Total", 0, f"ingreso_total_{fecha}")
with c2:
    cortesias = campo_entero("Cortesías", 0, f"ingreso_cortesias_{fecha}")
venta = max(0, total - cortesias)
c3.metric("Venta", venta, help="Se calcula automáticamente: Total − Cortesías")

# Guardado automático para conservar el trabajo al cambiar de página.
claves_borrador = [
    clave for clave in st.session_state
    if clave.startswith(("r_", "jm_", "maq_", "cat_", "cliente_", "cantidad_premios_", "pagos_monto_", "sobre_millon_", "ingreso_total_", "ingreso_cortesias_", "n_"))
]
st.session_state[BORRADOR_KEY] = {clave: st.session_state[clave] for clave in claves_borrador}
st.session_state["ultimo_guardado_cierre"] = datetime.now(ZoneInfo("America/Santiago")).strftime("%H:%M")
st.caption(f"✓ Borrador guardado · Último cambio: {st.session_state['ultimo_guardado_cierre']}")

def campo_completado(clave):
    valor = st.session_state.get(clave, "")
    if isinstance(valor, dict):
        valor = valor.get("value", "")
    return str(valor).strip() not in ("", "-", "-$")

def revisar_informe():
    problemas = []
    for indice, nombre in enumerate(presupuestos):
        if not campo_completado(f"r_{fecha}_{indice}"):
            problemas.append(f"Falta completar Resultado de {nombre}.")
    if not campo_completado(f"ingreso_total_{fecha}"):
        problemas.append("Falta completar Ingresos: Total.")
    if not campo_completado(f"ingreso_cortesias_{fecha}"):
        problemas.append("Falta completar Ingresos: Cortesías.")

    suma_jackpots = 0
    for indice in range(sobre_millon):
        numero = indice + 1
        if indice >= len(jackpots) or jackpots[indice][0] <= 0:
            problemas.append(f"Falta un monto válido en Jackpot {numero}.")
        else:
            suma_jackpots += jackpots[indice][0]
        if not st.session_state.get(f"maq_{fecha}_{indice}"):
            problemas.append(f"Falta seleccionar la máquina en Jackpot {numero}.")
        if not st.session_state.get(f"cat_{fecha}_{indice}"):
            problemas.append(f"Falta seleccionar la categoría en Jackpot {numero}.")
    if sobre_millon > 0 and not campo_completado(f"pagos_monto_{fecha}"):
        problemas.append("Falta completar el monto total de premios.")
    elif monto_pagos < suma_jackpots:
        problemas.append(
            f"El monto total de premios ({pesos(monto_pagos)}) debe ser igual o superior "
            f"a la suma de jackpots sobre $1 millón ({pesos(suma_jackpots)})."
        )
    return problemas

if st.button("Generar informe", type="primary", use_container_width=True):
    problemas = revisar_informe()
    if problemas:
        st.error("No se puede generar todavía. Revisa lo siguiente:")
        for problema in problemas:
            st.markdown(f"- {problema}")
    else:
        st.session_state["informe_png"] = crear_imagen(
            fecha, resultados, po, cantidad_pagos, monto_pagos, sobre_millon,
            novedades, jackpots, (total, cortesias, venta)
        )
        st.success("Informe revisado y generado correctamente.")

if "informe_png" in st.session_state:
    png = st.session_state["informe_png"]
    st.divider()
    with st.expander("Vista previa y descarga", expanded=False):
        st.image(png, use_container_width=True)
        st.download_button("Descargar PNG", png, file_name=f"informe_cierre_{fecha:%d-%m-%Y}.png", mime="image/png", use_container_width=True)
        b64 = base64.b64encode(png).decode("ascii")
        components.html(f"""
    <button id="copy" style="width:100%;padding:12px;border:0;border-radius:8px;background:#1787a8;color:white;font:600 16px sans-serif;cursor:pointer">Copiar imagen</button>
    <div id="msg" style="font:14px sans-serif;margin-top:8px;color:#334155"></div>
    <script>
    document.getElementById('copy').onclick = async () => {{
      const msg = document.getElementById('msg');
      try {{
        const blob = await (await fetch('data:image/png;base64,{b64}')).blob();
        await navigator.clipboard.write([new ClipboardItem({{'image/png': blob}})]);
        msg.textContent = 'Imagen copiada. Ya puedes pegarla en WhatsApp o correo.';
      }} catch (e) {{ msg.textContent = 'El navegador bloqueó la copia. Usa Descargar PNG.'; }}
    }};
    </script>""", height=72)

