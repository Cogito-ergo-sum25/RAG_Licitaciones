import streamlit as st
import json
from src.pdf_parser import extraer_texto_pdf
from src.excel_parser import procesar_licitacion_excel
from src.llm_engine import evaluar_con_ia, autocompletar_json_con_ia, obtener_top_3_equipos
from src.db_client import obtener_todos_los_productos, obtener_json_producto, guardar_json_producto, obtener_equipos_por_tag
from src.exporter import exportar_excel, exportar_word

# ==========================================
# PESTAÑA 1: EVALUADOR Y PRE-FILTRO
# ==========================================
def render_tab1():
    st.header("⚡ Escáner de Licitaciones y Pre-filtro")
    st.markdown("Pega los requisitos de la dependencia (SEDENA, ISSSTE, IMSS, etc.) y haremos un barrido rápido con tu inventario para encontrar a los mejores candidatos.")

    # --- MEMORIA DEL TEXTO ---
    if "texto_requisitos" not in st.session_state:
        st.session_state.texto_requisitos = ""
    if "ranking_rapido" not in st.session_state:
        st.session_state.ranking_rapido = []
        
    col_req, col_cat = st.columns([3, 1])
    
    with col_req:
        texto_input = st.text_area("1. Pega los requisitos técnicos a evaluar:", 
                                  value=st.session_state.texto_requisitos,
                                  height=200, 
                                  key="text_area_requisitos") 
        st.session_state.texto_requisitos = texto_input
    
    with col_cat:
        st.markdown("#### 🔍 Filtro")
        lista_tags_conocidos = ["Todos", "LAMPA", "MESAS", "CARRO", "REFRI", "ANES", "CUNA"]
        filtro_tag = st.selectbox("Categoría a escanear:", lista_tags_conocidos)
            
    # ==========================================
    # FASE 1: BARRIDO RÁPIDO (LA FÓRMULA)
    # ==========================================
    st.divider()
    if st.button("🔎 Ejecutar Barrido Rápido (Scoring)", type="primary", width='stretch'):
        if not st.session_state.texto_requisitos.strip():
            st.warning("⚠️ Pega los requisitos técnicos primero.")
        else:
            equipos_a_evaluar = obtener_equipos_por_tag(filtro_tag) if filtro_tag != "Todos" else []
            
            if not equipos_a_evaluar:
                st.error("No hay equipos o seleccionaste 'Todos' (elige una categoría específica).")
            else:
                with st.spinner(f"Escaneando {len(equipos_a_evaluar)} equipos a máxima velocidad..."):
                    from src.llm_engine import escaner_rapido_score
                    import json
                    
                    resultados_scoring = []
                    progress_bar = st.progress(0)
                    
                    for i, equipo in enumerate(equipos_a_evaluar):
                        json_str = json.dumps(equipo['json_limpio'], ensure_ascii=False) if isinstance(equipo['json_limpio'], dict) else equipo['json_limpio']
                        
                        # Llamamos al escáner rápido
                        score_data = escaner_rapido_score(st.session_state.texto_requisitos, json_str)
                        
                        if score_data:
                            score_data['equipo'] = equipo['modelo']
                            score_data['marca'] = equipo['marca']
                            score_data['id'] = equipo['id_producto']
                            resultados_scoring.append(score_data)
                            
                        progress_bar.progress((i + 1) / len(equipos_a_evaluar))
                    
                    # Guardamos los resultados en memoria y ordenamos por Score
                    if resultados_scoring:
                        st.session_state.ranking_rapido = sorted(resultados_scoring, key=lambda x: x.get('score_compatibilidad', 0), reverse=True)
                        st.rerun()

    # --- MOSTRAR LA TABLA DE POSICIONES ---
    if st.session_state.ranking_rapido:
        st.subheader("📊 Leaderboard: Mejores Candidatos")
        
        # Preparamos los datos para una tabla limpia de Pandas
        tabla_datos = []
        for res in st.session_state.ranking_rapido:
            alertas = " | ".join(res.get('alertas_rojas', [])) if res.get('alertas_rojas') else "Ninguna"
            
            tabla_datos.append({
                "Score": f"{res.get('score_compatibilidad', 0)}%",
                "Marca": res.get('marca', 'N/A'),
                "Modelo": res.get('equipo', 'N/A'),
                "Resumen": res.get('motivo_principal', ''),
                "Focos Rojos": alertas,
                "ID": res.get('id', '')
            })
            
        st.dataframe(tabla_datos, use_container_width=True, hide_index=True)
        
        # ==========================================
        # FASE 2: DICTAMEN EXHAUSTIVO DEL GANADOR
        # ==========================================
        st.divider()
        st.markdown("### 🥇 Análisis Exhaustivo")
        st.write("Selecciona el equipo ganador del barrido para generar la matriz de cumplimiento (Semáforos) y exportar a Word/Excel.")
        
        # Creamos un diccionario para el selectbox
        opciones_ganador = {f"{r.get('Score', '0')}% - {r.get('Marca', '')} {r.get('Modelo', '')}": r.get('ID') for r in st.session_state.ranking_rapido}
        equipo_elegido_key = st.selectbox("Elige el equipo a dictaminar:", list(opciones_ganador.keys()))
        
        if st.button("🚀 Generar Dictamen Oficial (Semáforos)", type="secondary"):
            id_ganador = opciones_ganador[equipo_elegido_key]
            
            with st.spinner("Creando matriz exhaustiva punto por punto..."):
                from src.llm_engine import evaluar_cumplimiento_ia 
                from src.db_client import obtener_json_producto
                
                json_db = obtener_json_producto(id_ganador)
                
                if json_db:
                    dictamen_completo = evaluar_cumplimiento_ia(st.session_state.texto_requisitos, json_db)
                    
                    if dictamen_completo:
                        st.success("¡Dictamen generado con éxito!")
                        st.markdown(f"**Veredicto General:** {dictamen_completo.get('veredicto_general', '')}")
                        
                        datos_matriz = []
                        for punto in dictamen_completo.get('puntos_evaluados', []):
                            datos_matriz.append({
                                "Estado": punto.get('semaforo', '⚪'),
                                "Requisito Licitación": punto.get('requisito_licitacion', punto.get('requisito_imss', '')), 
                                "Especificación Equipo": punto.get('especificacion_equipo', ''),
                                "Justificación": punto.get('justificacion', '')
                            })
                        st.dataframe(datos_matriz, use_container_width=True, hide_index=True)