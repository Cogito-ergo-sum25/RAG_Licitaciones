import streamlit as st

# Importamos las funciones de renderizado de nuestras pestañas
from src.tabs.tab1_evaluador import render_tab1
from src.tabs.tab2_productos import render_tab2
from src.tabs.tab3_plantillas import render_tab3

# Configuración global de la página
st.set_page_config(page_title="Sistema Pericial AI", layout="wide")

st.title("🏥 Sistema de Evaluación y Catálogo Biomédico")

# Declaramos las 3 pestañas
tab1, tab2, tab3 = st.tabs([
    "⚡ 1. Evaluador de Licitaciones", 
    "📦 2. CRUD Productos", 
    "⚙️ 3. Reglas y Plantillas"
])

# Ejecutamos cada módulo en su respectiva pestaña
with tab1:
    render_tab1()

with tab2:
    render_tab2()

with tab3:
    render_tab3()

