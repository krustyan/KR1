import streamlit as st

consulta = st.Page(
    "app_pages/consulta_ppto.py",
    title="CONSULTA PPTO",
    icon="📊",
    default=True,
)
informe = st.Page(
    "pages/Informe_de_cierre.py",
    title="INFORME DE CIERRE",
    icon="📝",
)

pagina = st.navigation([consulta, informe])
pagina.run()
