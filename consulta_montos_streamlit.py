import streamlit as st

consulta = st.Page(
    "app_pages/consulta_ppto.py",
    title="CONSULTA PPTO",
    icon="📊",
    default=True,
)
parcial = st.Page(
    "app_pages/informe_parcial.py",
    title="INFORME PARCIAL",
    icon="⏱️",
)
informe = st.Page(
    "pages/Informe_de_cierre.py",
    title="INFORME DE CIERRE",
    icon="📝",
)

pagina = st.navigation([consulta, parcial, informe])
pagina.run()
