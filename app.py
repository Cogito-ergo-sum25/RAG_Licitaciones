import streamlit as st
from src.excel_parser import procesar_licitacion_excel
from src.llm_engine import evaluar_con_ia

# Configuración de la página
st.set_page_config(page_title="Evaluador de Licitaciones", page_icon="🏥", layout="wide")

st.title("🏥 Sistema Evaluador de Licitaciones Intevi")
st.markdown("Sube tu archivo de propuestas en Excel y evalúa los anexos técnicos usando IA local.")

# 1. Subida del archivo
archivo_excel = st.file_uploader("Sube tu archivo Propuestas.xlsx", type=['xlsx'])

if archivo_excel is not None:
    # Mostramos un spinner mientras lee las hojas
    with st.spinner('Procesando hojas del Excel...'):
        diccionario_partidas = procesar_licitacion_excel(archivo_excel)
    
    if diccionario_partidas:
        st.success(f"¡Excel cargado! Se encontraron {len(diccionario_partidas)} partidas.")
        
        # 2. Selector de Partida
        lista_hojas = list(diccionario_partidas.keys())
        partida_seleccionada = st.selectbox("Selecciona la partida a evaluar:", lista_hojas)
        
        texto_partida = diccionario_partidas[partida_seleccionada]
        
        # Mostramos un preview de lo que se va a evaluar
        with st.expander("Ver texto extraído de la licitación"):
            st.text(texto_partida[:1000] + "\n... [Texto recortado para vista previa]")

        st.divider()
        
        # 3. Simulación de selección de equipo (Aquí luego conectaremos tu db_client.py)
        st.subheader("Selección de Equipo Propuesto")
        equipo_propuesto = st.selectbox("Selecciona el equipo para hacer el match:", 
                                        ["CEABIS CEACA09 (Refrigerador Mortuorio)", "AMTAI T800 (Mesa Quirúrgica)", "ORDISI FLH (Lámpara)"])
        
        # JSON Simulado para la prueba visual
        json_prueba = """
        {
          "marca": "CEABIS",
          "modelo": "CEACA09",
          "tipo": "Refrigerador para 2 cadáveres",
          "puertas": "2 de acceso lateral",
          "material_interior_exterior": "Acero inoxidable AISI-304",
          "rango_temperatura_celsius": {"min": -5, "max": 5},
          "capacidad_carga_por_bandeja_kg": 200
        }
        """

        # 4. Botón de Ejecución de IA
        if st.button("🚀 Evaluar con Inteligencia Artificial", type="primary"):
            with st.spinner("Tu RX 7600 XT está analizando los datos..."):
                # Recortamos a 1000 caracteres solo para esta prueba rápida
                resultado = evaluar_con_ia(texto_partida[:1000], json_prueba, modelo="llama3.1")
                
                if resultado:
                    st.subheader("Dictamen Técnico")
                    st.markdown(resultado)