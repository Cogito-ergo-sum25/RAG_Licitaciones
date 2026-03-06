import streamlit as st
import json
from src.excel_parser import procesar_licitacion_excel
from src.llm_engine import evaluar_con_ia
from src.db_client import obtener_todos_los_productos, obtener_json_producto, guardar_json_producto, obtener_equipos_por_tag

st.set_page_config(page_title="Evaluador Intevi", page_icon="🏥", layout="wide")

st.title("🏥 Sistema Evaluador de Licitaciones Intevi")

# --- CREAMOS DOS PESTAÑAS ---
tab1, tab2 = st.tabs(["🚀 Modo Evaluación IA", "📦 Gestión de Catálogos (CRUD JSON)"])

# ==========================================
# PESTAÑA 2: EL CRUD DE TUS PRODUCTOS
# ==========================================
with tab2:
    st.header("Gestor de Especificaciones Técnicas")
    st.markdown("Alimenta tu base de datos con las especificaciones. Usa las plantillas para no olvidar ningún campo importante.")
    
    productos = obtener_todos_los_productos()
    
    if not productos:
        st.warning("No se encontraron productos en la base de datos.")
    else:
        # --- SISTEMA DE FILTROS ---
        st.markdown("#### 🔍 Filtros de Búsqueda")
        col_f1, col_f2 = st.columns(2)
        
        lista_marcas = ["Todas"] + sorted(list(set(str(p['marca']) for p in productos if p['marca'])))
        lista_tipos = ["Todos"] + sorted(list(set(str(p['tipo']) for p in productos if p['tipo'])))
        
        with col_f1:
            filtro_marca = st.selectbox("Filtrar por Marca:", lista_marcas)
        with col_f2:
            filtro_tipo = st.selectbox("Filtrar por Tipo:", lista_tipos)
            
        productos_filtrados = productos
        if filtro_marca != "Todas":
            productos_filtrados = [p for p in productos_filtrados if p['marca'] == filtro_marca]
        if filtro_tipo != "Todos":
            productos_filtrados = [p for p in productos_filtrados if p['tipo'] == filtro_tipo]
            
        st.divider()
        
        if not productos_filtrados:
            st.info("No hay productos que coincidan con estos filtros.")
        else:
            # --- SELECCIÓN DE PRODUCTO ---
            opciones_productos = {f"[{p['marca']}] {p['nombre']} - {p['modelo']} (ID: {p['id_producto']})": p['id_producto'] for p in productos_filtrados}
            producto_seleccionado = st.selectbox("1. Selecciona el Producto a editar:", list(opciones_productos.keys()))
            id_prod = opciones_productos[producto_seleccionado]
            
            # Obtenemos el JSON actual de la base de datos
            json_actual = obtener_json_producto(id_prod)
            
            # Obtenemos el JSON actual
            json_actual = obtener_json_producto(id_prod)
            
            # --- MANEJO DE MEMORIA DE STREAMLIT (SESSION STATE) ---
            # Si cambiamos de producto, o si es la primera vez que entramos, cargamos el JSON de la BD a la memoria
            if "id_producto_actual" not in st.session_state or st.session_state.id_producto_actual != id_prod:
                st.session_state.id_producto_actual = id_prod
                st.session_state.json_editor = json_actual

            # --- EL MOTOR DE PLANTILLAS ---
            st.write("¿El JSON está vacío? Carga una estructura base rica en especificaciones:")
            col1, col2, col3, col4 = st.columns(4)
            
            if col1.button("💡 Plantilla Lámparas (LAMPA)"):
                plantilla = {
                    "tag_licitacion": "LAMPA",
                    "tipo_lampara": "Examinación / Quirúrgica / Fototerapia",
                    "tecnologia_iluminacion": "LED",
                    "cantidad_minima_leds": 0,
                    "potencia_maxima_watts": 0,
                    "intensidad_luminosa_luxes": 0,
                    "temperatura_color_kelvin": 0,
                    "vida_util_horas": 0,
                    "control_intensidad_iluminacion": True,
                    "longitud_brazo_flexible_cm": 0,
                    "diametro_campo_iluminacion_cm": {"min": 0, "max": 0},
                    "mango_posicionamiento_una_mano": True,
                    "fototerapia_longitud_onda_nm": {"min": 0, "max": 0},
                    "fototerapia_irradiacion_microwatts_cm2_nm": 0,
                    "fototerapia_superficie_efectiva_cm": {"min": 0, "max": 0},
                    "ajuste_altura_e_inclinacion": True,
                    "pedestal_rodable_con_frenos": True,
                    "contador_de_horas_integrado": True,
                    "compatibilidad_radiometro_misma_marca": False
                }
                st.session_state.json_editor = json.dumps(plantilla, indent=4, ensure_ascii=False)
                st.rerun()
                
            if col2.button("🛏️ Plantilla Mesa Quirúrgica (MESAS)"):
                plantilla = {
                    "tag_licitacion": "MESAS",
                    "tipo_equipo": "Mesa Quirúrgica Electrohidráulica",
                    "control_por_microprocesador": True,
                    "capacidad_carga_kg": 0,
                    "sistema_frenos_pivotes_anclaje": True,
                    "longitud_total_cm": 0,
                    "material_estructura_y_cubiertas": "Acero inoxidable o acero al cromo níquel",
                    "superficie_radiotransparente": True,
                    "cantidad_secciones": 5,
                    "posicion_nefrectomia_elevador_rinon": False,
                    "piernas_desmontables_abatibles_grados": 0,
                    "movimiento_tijera_piernas": False,
                    "cabecera_ajuste_flexion_grados": 0,
                    "rango_elevacion_descenso_cm": {"min": 0, "max": 0},
                    "grados_fowler_semifowler": {"min": 0, "max": 0},
                    "posicion_kraske_navaja_sevillana": True,
                    "grados_trendelenburg": 0,
                    "grados_trendelenburg_inverso": 0,
                    "grados_inclinacion_lateral": 0,
                    "tablero_giratorio": False,
                    "acceso_arco_en_c_desplazamiento_longitudinal_cm": 0,
                    "sistema_emergencia_panel_columna": True,
                    "sistema_emergencia_bombeo_hidraulico_manual": True,
                    "retorno_automatico_horizontal": True,
                    "bateria_respaldo_indicador_carga": True,
                    "cojines_conductivos_antiestaticos_sin_costuras": True,
                    "accesorios_incluidos_cirugia_general": [],
                    "accesorios_incluidos_ortopedia": []
                }
                st.session_state.json_editor = json.dumps(plantilla, indent=4, ensure_ascii=False)
                st.rerun()
                
            if col3.button("❄️ Plantilla Refri (REFRI)"):
                plantilla = {
                    "tag_licitacion": "REFRI",
                    "tipo_equipo": "Refrigerador Mortuorio",
                    "capacidad_cadaveres": 0,
                    "gavetas_acceso_lateral": False,
                    "material_interior": "Acero Inoxidable AISI-304",
                    "material_exterior": "Acero Inoxidable AISI-304",
                    "rango_temperatura_celsius": {"min": 0, "max": 0},
                    "capacidad_carga_por_bandeja_kg": 0,
                    "tipo_gas_refrigerante": "",
                    "compresor_especificaciones": "",
                    "sistema_alarmas_audibles_visuales": True
                }
                st.session_state.json_editor = json.dumps(plantilla, indent=4, ensure_ascii=False)
                st.rerun()
                
            if col4.button("🛒 Plantilla Carro (CARRO)"):
                plantilla = {
                    "tag_licitacion": "CARRO",
                    "tipo_equipo": "Carro Camilla",
                    "capacidad_carga_kg": 0,
                    "dimensiones_cm": {"largo": {"min": 0, "max": 0}, "ancho": {"min": 0, "max": 0}, "altura": {"min": 0, "max": 0}},
                    "material_fabricacion": "Acero Inoxidable AISI-304",
                    "borde_perimetral_antiderrames": True,
                    "ruedas_cantidad": 4,
                    "diametro_ruedas_cm": 0,
                    "frenos_cantidad": 2,
                    "maneral_conduccion": True
                }
                st.session_state.json_editor = json.dumps(plantilla, indent=4, ensure_ascii=False)
                st.rerun()

            # --- AUTOCOMPLETADO CON IA ---
            st.divider()
            st.markdown("### 🤖 Autocompletado Inteligente")
            
            pdf_catalogo = st.file_uploader("Sube el PDF del equipo (Ej. Catálogo_AMTAI.pdf)", type=['pdf'])
            
            if pdf_catalogo and st.button("✨ Autocompletar con IA"):
                with st.spinner("Leyendo PDF y extrayendo datos técnicos..."):
                    import pdfplumber
                    texto_pdf = ""
                    with pdfplumber.open(pdf_catalogo) as pdf:
                        for pagina in pdf.pages:
                            texto_pagina = pagina.extract_text()
                            if texto_pagina:
                                texto_pdf += texto_pagina + "\n"
                    
                    from src.llm_engine import autocompletar_json_con_ia
                    # Le mandamos a la IA lo que sea que esté en la memoria actual
                    nuevo_json = autocompletar_json_con_ia(texto_pdf, st.session_state.json_editor)
                    
                    if nuevo_json:
                        # Guardamos el resultado mágico en la memoria temporal
                        st.session_state.json_editor = nuevo_json 
                        st.rerun() # Refrescamos para que se vea en el cuadro de texto

            # --- ÁREA DE EDICIÓN Y GUARDADO ---
            st.divider()
            st.write("2. Edita las especificaciones técnicas:")
            
            # El cuadro de texto está amarrado a la memoria temporal (session_state)
            json_editado = st.text_area("Formato JSON:", value=st.session_state.json_editor, height=350)
            
            if st.button("💾 Guardar Especificaciones en Base de Datos", type="primary"):
                exito, mensaje = guardar_json_producto(id_prod, json_editado)
                if exito:
                    st.success(mensaje)
                    # Actualizamos la memoria para que no haya desajustes
                    st.session_state.json_editor = json_editado
                else:
                    st.error(mensaje)


# ==========================================
# PESTAÑA 1: EL EVALUADOR DE LICITACIONES
# ==========================================
with tab1:
    st.markdown("Sube tu archivo de propuestas en Excel y evalúa los anexos técnicos contra tu inventario real.")

    archivo_excel = st.file_uploader("Sube tu archivo Propuestas.xlsx", type=['xlsx'])

    if archivo_excel is not None:
        with st.spinner('Procesando hojas del Excel...'):
            diccionario_partidas = procesar_licitacion_excel(archivo_excel)
        
        if diccionario_partidas:
            st.success(f"¡Excel cargado! Se encontraron {len(diccionario_partidas)} partidas.")
            
            # Selector de Partida
            lista_hojas = list(diccionario_partidas.keys())
            partida_seleccionada = st.selectbox("Selecciona la partida a evaluar:", lista_hojas)
            
            # --- LA MAGIA DEL AUTO-FILTRO ---
            # Cortamos el nombre "I-MESAS-5316..." en los guiones y agarramos "MESAS"
            partes_nombre = partida_seleccionada.split("-")
            tag_detectado = partes_nombre[1] if len(partes_nombre) > 1 else "DESCONOCIDO"
            
            st.info(f"🧠 **Filtro Inteligente:** Se detectó la categoría `{tag_detectado}`. Buscando equipos compatibles en tu inventario...")
            
            texto_partida = diccionario_partidas[partida_seleccionada]
            
            with st.expander("Ver texto original extraído de la licitación"):
                st.text(texto_partida)

            st.divider()
            
            # Buscamos en la BD los equipos que hagan match con el Tag
            equipos_compatibles = obtener_equipos_por_tag(tag_detectado)
            
            if not equipos_compatibles:
                st.warning(f"No tienes equipos guardados con el tag '{tag_detectado}' en tu base de datos. ¡Ve a la pestaña de Gestión de Catálogos a darlos de alta!")
            else:
                st.subheader("Selección de Equipo Propuesto")
                
                # Armamos el menú desplegable con las marcas reales
                opciones_equipos = {f"[{e['marca']}] {e['nombre']} - {e['modelo']}": e for e in equipos_compatibles}
                equipo_seleccionado = st.selectbox("Selecciona el equipo para hacer el match:", list(opciones_equipos.keys()))
                
                # Extraemos el JSON real del equipo seleccionado
                datos_equipo_real = opciones_equipos[equipo_seleccionado]
                json_para_ia = json.dumps(datos_equipo_real['json_limpio'], indent=4, ensure_ascii=False)
                
                with st.expander("Ver especificaciones del equipo seleccionado (JSON)"):
                    st.code(json_para_ia, language='json')

                # Evaluamos de verdad
                if st.button("🚀 Evaluar Partida vs Equipo", type="primary", key="btn_evaluar"):
                    with st.spinner("Tu RX 7600 XT está cruzando los datos punto por punto con Qwen..."):
                        # Le mandamos el texto completo de la partida y el JSON real. 
                        # Sugiero usar qwen2.5:14b aquí también porque razona mejor la lógica de "Cumple / No Cumple"
                        resultado = evaluar_con_ia(texto_partida, json_para_ia, modelo="qwen2.5:14b")
                        
                        if resultado:
                            st.subheader("Dictamen Técnico")
                            st.markdown(resultado)