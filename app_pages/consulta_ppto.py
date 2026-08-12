import streamlit as st
import pandas as pd
import os
import time
import json
import streamlit.components.v1 as components

FILE_PATH = "CIERRE_PPTO_2025.xlsx"
SHEET_NAME = "bases"

dias_es = {'Monday':'Lunes','Tuesday':'Martes','Wednesday':'Miércoles','Thursday':'Jueves','Friday':'Viernes','Saturday':'Sábado','Sunday':'Domingo'}
meses_es = {1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}

def formatear_monto(valor):
    try: valor = int(valor)
    except: valor = 0
    return f"${valor:,.0f}".replace(",", ".")

def to_int(v):
    if pd.isna(v): return 0
    if isinstance(v, str): v = v.replace(".", "").replace(",", ".").strip()
    try: return int(float(v))
    except: return 0

def tarjeta(icono, titulo, monto, clase):
    return f'<div class="metric-card {clase}"><div class="metric-icon">{icono}</div><div class="metric-title">{titulo}</div><div class="metric-value">{formatear_monto(monto)}</div></div>'


def boton_copiar_ppto(fecha_texto, valores):
    datos = json.dumps(
        {
            "fecha": fecha_texto,
            "items": [
                {"titulo": "Win TGM", "valor": formatear_monto(valores[0]), "color": "#38d879", "fondo": "#092d23"},
                {"titulo": "Coin In", "valor": formatear_monto(valores[1]), "color": "#4c9cff", "fondo": "#0c2038"},
                {"titulo": "Win Mesas", "valor": formatear_monto(valores[2]), "color": "#b45eff", "fondo": "#281b3d"},
                {"titulo": "Drop Mesas", "valor": formatear_monto(valores[3]), "color": "#f2be2d", "fondo": "#302a17"},
            ],
        },
        ensure_ascii=False,
    )
    plantilla = """
    <button id="copiar" style="width:100%;height:38px;border:0;border-radius:9px;background:#1787a8;color:white;font:600 14px sans-serif;cursor:pointer">📋 Copiar PPTO</button>
    <div id="mensaje" style="font:12px sans-serif;color:#94a3b8;margin-top:3px;text-align:center"></div>
    <script>
    const datos = __DATOS__;
    const boton = document.getElementById('copiar');
    const mensaje = document.getElementById('mensaje');
    const redondeado = (ctx,x,y,w,h,r) => {
      ctx.beginPath(); ctx.roundRect(x,y,w,h,r); ctx.fill();
    };
    boton.onclick = async () => {
      const canvas = document.createElement('canvas');
      canvas.width = 900; canvas.height = 470;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#0e1117'; ctx.fillRect(0,0,900,470);
      ctx.fillStyle = '#f8fafc'; ctx.font = '700 30px Arial';
      ctx.fillText('PPTO DE LA JORNADA', 34, 52);
      ctx.fillStyle = '#cbd5e1'; ctx.font = '600 23px Arial';
      ctx.fillText(datos.fecha, 34, 88);
      datos.items.forEach((item, i) => {
        const col = i % 2, fila = Math.floor(i / 2);
        const x = 34 + col * 421, y = 118 + fila * 158;
        ctx.fillStyle = item.fondo; redondeado(ctx,x,y,399,136,17);
        ctx.fillStyle = item.color; ctx.fillRect(x,y+132,399,4);
        ctx.fillStyle = '#f8fafc'; ctx.font = '700 21px Arial';
        ctx.fillText(item.titulo, x+22, y+43);
        ctx.fillStyle = item.color; ctx.font = '800 32px Arial';
        ctx.fillText(item.valor, x+22, y+94);
      });
      try {
        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
        await navigator.clipboard.write([new ClipboardItem({'image/png': blob})]);
        mensaje.textContent = 'Imagen copiada';
        boton.textContent = '✓ PPTO copiado';
      } catch (error) {
        mensaje.textContent = 'El navegador bloqueó la copia';
      }
    };
    </script>
    """
    components.html(plantilla.replace("__DATOS__", datos), height=58)

@st.cache_data
def load_data(file_path: str, mtime: float):
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(xls, sheet_name=SHEET_NAME)
    df.columns = df.iloc[0]
    df = df[1:].copy()
    df.columns = [str(c).strip() for c in df.columns]
    df.rename(columns={"dia":"Fecha","WIN TGM":"Win TGM","COIN IN":"Coin In","WIN MESAS":"Win Mesas","DROP":"Drop Mesas"}, inplace=True)
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce", dayfirst=True).dt.normalize()
    return df

st.set_page_config(page_title="PPTO Enjoy Los Ángeles", page_icon="📊", layout="centered")
st.markdown("""
<style>
.block-container{padding-top:.7rem;padding-bottom:1rem;max-width:760px}.main-title{font-size:2rem;font-weight:800;margin:0 0 .25rem 0}.date-title{font-size:1.25rem;font-weight:750;margin:.65rem 0}.metric-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.65rem;width:100%}.metric-card{border-radius:16px;padding:.85rem;min-height:122px;border:1px solid rgba(255,255,255,.10);box-shadow:0 6px 18px rgba(0,0,0,.16);display:flex;flex-direction:column;justify-content:center;overflow:hidden}.metric-icon{font-size:1.6rem;line-height:1;margin-bottom:.55rem}.metric-title{font-size:.95rem;font-weight:700;margin-bottom:.4rem;white-space:nowrap}.metric-value{font-size:clamp(1.05rem,4.8vw,1.65rem);font-weight:850;line-height:1.08;letter-spacing:-.035em;white-space:nowrap}.tgm{background:linear-gradient(145deg,rgba(12,72,50,.40),rgba(7,26,22,.72));border-bottom:3px solid #28c76f}.tgm .metric-value{color:#38d879}.coin{background:linear-gradient(145deg,rgba(20,55,95,.45),rgba(8,23,42,.76));border-bottom:3px solid #4097ff}.coin .metric-value{color:#4c9cff}.mesas{background:linear-gradient(145deg,rgba(70,42,105,.42),rgba(25,19,42,.76));border-bottom:3px solid #ad55ff}.mesas .metric-value{color:#b45eff}.drop{background:linear-gradient(145deg,rgba(90,72,22,.38),rgba(34,30,17,.76));border-bottom:3px solid #f1be28}.drop .metric-value{color:#f2be2d}div[data-testid="stDateInput"] input{border-radius:12px}div[data-testid="stDateInput"]{margin-bottom:-.35rem}div[data-testid="stButton"] button{padding-top:.25rem;padding-bottom:.25rem;min-height:2.2rem}@media(max-width:640px){.block-container{padding-left:.8rem;padding-right:.8rem;padding-top:.45rem}.main-title{font-size:1.7rem}.date-title{font-size:1.05rem;margin:.5rem 0 .55rem 0}.metric-grid{gap:.5rem}.metric-card{min-height:108px;border-radius:14px;padding:.7rem}.metric-icon{font-size:1.35rem;margin-bottom:.4rem}.metric-title{font-size:.82rem;margin-bottom:.28rem}.metric-value{font-size:clamp(.93rem,4.35vw,1.25rem)}}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 PPTO</div>', unsafe_allow_html=True)
st.page_link("pages/Informe_de_cierre.py", label="📝 Generar informe de cierre")
colA,colB=st.columns([1,2.2])
with colA:
    if st.button("🔄 Recargar"):
        st.cache_data.clear(); st.rerun()
with colB:
    if os.path.exists(FILE_PATH): st.caption(f"Actualizado: {time.strftime('%d/%m/%Y %H:%M',time.localtime(os.path.getmtime(FILE_PATH)))}")

st.markdown("📆 **Selecciona una fecha:**")
fecha=st.date_input("",format="DD/MM/YYYY",label_visibility="collapsed")
dia_semana=dias_es.get(fecha.strftime('%A'),fecha.strftime('%A')); dia=fecha.day; mes=meses_es.get(fecha.month,str(fecha.month)); anio=fecha.year
fecha_texto = f"{dia_semana} {dia:02d} de {mes} de {anio}"
col_fecha, col_copiar = st.columns([2.5, 1])
with col_fecha:
    st.markdown(f'<div class="date-title">📅 {fecha_texto}</div>', unsafe_allow_html=True)

try:
    if not os.path.exists(FILE_PATH): raise FileNotFoundError
    df=load_data(FILE_PATH,os.path.getmtime(FILE_PATH)); df_filtrado=df[df["Fecha"].dt.date==fecha]
    if not df_filtrado.empty:
        if len(df_filtrado)>1: st.warning(f"⚠️ Hay {len(df_filtrado)} filas para esta fecha. Se mostrará la primera.")
        fila=df_filtrado.iloc[0]
        win_tgm=to_int(fila.get("Win TGM")); coin_in=to_int(fila.get("Coin In")); win_mesas=to_int(fila.get("Win Mesas")); drop_mesas=to_int(fila.get("Drop Mesas"))
        with col_copiar:
            boton_copiar_ppto(fecha_texto, (win_tgm, coin_in, win_mesas, drop_mesas))
        tarjetas_html='<div class="metric-grid">'+tarjeta("🎰","Win TGM",win_tgm,"tgm")+tarjeta("💵","Coin In",coin_in,"coin")+tarjeta("🎲","Win Mesas",win_mesas,"mesas")+tarjeta("🪙","Drop Mesas",drop_mesas,"drop")+'</div>'
        st.markdown(tarjetas_html,unsafe_allow_html=True)
    else: st.warning("⚠️ No se encontraron datos para la fecha seleccionada.")
except FileNotFoundError: st.error("❌ El archivo 'CIERRE_PPTO_2025.xlsx' no se encontró.")
except Exception as e: st.error(f"❌ Error: {e}")
