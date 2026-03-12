import streamlit as st
import json
import os
from src.pdf_parser import extraer_texto_pdf
from src.llm_engine import autocompletar_json_con_ia
from src.db_client import obtener_todos_los_productos, obtener_json_producto, guardar_json_producto

def render_tab2():
    st.header("Gestor de Especificaciones Técnicas")
    st.markdown("Alimenta tu base de datos con las especificaciones. Usa las plantillas para no olvidar ningún campo importante.")
    
    productos = obtener_todos_los_productos()
    
    if not productos:
        st.warning("No se encontraron productos en la base de datos.")
    else:
        # --- SISTEMA DE FILTROS ---
        st.markdown("#### 🔍 Filtros de Búsqueda")
        
        # Ahora usamos 3 columnas para incluir la Clasificación
        col_f1, col_f2, col_f3 = st.columns(3)
        
        # Obtenemos las listas únicas, protegiendo con .get() por si algún dato es nulo
        lista_marcas = ["Todas"] + sorted(list(set(str(p.get('marca', '')) for p in productos if p.get('marca'))))
        lista_tipos = ["Todos"] + sorted(list(set(str(p.get('tipo', '')) for p in productos if p.get('tipo'))))
        lista_clasificaciones = ["Todas"] + sorted(list(set(str(p.get('clasificacion', '')) for p in productos if p.get('clasificacion'))))
        
        with col_f1:
            filtro_marca = st.selectbox("Filtrar por Marca:", lista_marcas)
        with col_f2:
            filtro_tipo = st.selectbox("Filtrar por Tipo:", lista_tipos)
        with col_f3:
            filtro_clasificacion = st.selectbox("Filtrar por Clasificación:", lista_clasificaciones)
            
        # Aplicamos los filtros en cascada
        productos_filtrados = productos
        if filtro_marca != "Todas":
            productos_filtrados = [p for p in productos_filtrados if p.get('marca') == filtro_marca]
        if filtro_tipo != "Todos":
            productos_filtrados = [p for p in productos_filtrados if p.get('tipo') == filtro_tipo]
        if filtro_clasificacion != "Todas":
            productos_filtrados = [p for p in productos_filtrados if p.get('clasificacion') == filtro_clasificacion]
            
        st.divider()
        
        if not productos_filtrados:
            st.info("No hay productos que coincidan con estos filtros.")
        else:
            # --- SELECCIÓN DE PRODUCTO (NUEVO FORMATO) ---
            # Usamos nombre_corto (si no existe, usamos el nombre normal como respaldo)
            opciones_productos = {}
            for p in productos_filtrados:
                marca = p.get('marca', 'S/M')
                # Priorizamos nombre_corto, si está vacío usamos nombre
                nombre_mostrar = p.get('nombre_corto') if p.get('nombre_corto') else p.get('nombre', 'Sin Nombre')
                sku = p.get('sku', 'Sin SKU')
                id_prod = p.get('id_producto')
                
                etiqueta = f"[{marca}] {nombre_mostrar} - {sku} (ID: {id_prod})"
                opciones_productos[etiqueta] = id_prod
                
            producto_seleccionado = st.selectbox("1. Selecciona el Producto a editar:", list(opciones_productos.keys()))
            id_prod = opciones_productos[producto_seleccionado]
            datos_prod = next(p for p in productos_filtrados if p['id_producto'] == id_prod)
            
            st.markdown("### 📦 Ficha Comercial del Equipo")
            # Dividimos en 2 columnas: 1/3 para imagen, 2/3 para datos
            col_img, col_datos = st.columns([1, 2])
            
            with col_img:
                if datos_prod.get('imagen_url'):
                    st.image(datos_prod['imagen_url'], width='stretch')
                else:
                    st.info("📷 Sin imagen disponible")
                    
                # Botón directo al PDF si existe
                if datos_prod.get('ficha_tecnica_url'):
                    st.link_button("📄 Ver Ficha Técnica Original", datos_prod['ficha_tecnica_url'], use_container_width=True)

            with col_datos:
                st.markdown("##### Información General")
                
                # Cambiamos a 2 columnas con texto limpio (Markdown) en lugar de metrics
                c1, c2 = st.columns(2)
                
                with c1:
                    st.markdown(f"**📌 Marca:** {datos_prod.get('marca') or 'N/A'}")
                    st.markdown(f"**🏷️ Modelo:** {datos_prod.get('modelo') or 'N/A'}")
                    st.markdown(f"**📦 SKU:** {datos_prod.get('sku') or 'N/A'}")
                
                with c2:
                    st.markdown(f"**⚙️ Tipo:** {datos_prod.get('tipo') or 'N/A'}")
                    st.markdown(f"**📑 Clase:** {datos_prod.get('clasificacion') or 'N/A'}")
                    st.markdown(f"**🌎 Origen:** {datos_prod.get('pais') or 'N/A'}")
                
                st.markdown("---")
                # Certificaciones a todo lo ancho
                st.markdown(f"**🏅 Certificaciones:** {datos_prod.get('certificaciones') or 'Ninguna registrada'}")
                
            st.divider()

            # --- MANEJO DE MEMORIA DE STREAMLIT (EL FIX SUPREMO) ---
            json_actual = obtener_json_producto(id_prod)
            texto_inicial = json_actual if json_actual else "{}"
            
            # Definimos la llave única que tendrá el cuadro de texto para este producto
            area_key = f"area_{id_prod}"
            
            # Si cambiamos de producto, inyectamos el JSON de la BD directo al cuadro de texto
            if "id_producto_actual" not in st.session_state or st.session_state.id_producto_actual != id_prod:
                st.session_state.id_producto_actual = id_prod
                st.session_state.json_editor = texto_inicial
                # Inyección directa a la llave del widget
                st.session_state[area_key] = texto_inicial

            # ==================================================
            # --- EL MOTOR DE PLANTILLAS DINÁMICO (LA MAGIA) ---
            # ==================================================
            st.write("¿El JSON está vacío? Carga una estructura base rica en especificaciones:")
            
            ruta_plantillas = "plantillas_equipos.json"
            if os.path.exists(ruta_plantillas):
                with open(ruta_plantillas, "r", encoding="utf-8") as f:
                    catalogo_plantillas = json.load(f)
                
                col_sel, col_btn = st.columns([3, 1])
                
                with col_sel:
                    # Extraemos los nombres de los botones para el Selectbox
                    opciones_mostrar = {datos.get("nombre_boton", f"Plantilla {tag}"): tag for tag, datos in catalogo_plantillas.items()}
                    seleccion_plantilla = st.selectbox("Selecciona la categoría del equipo:", list(opciones_mostrar.keys()), label_visibility="collapsed")
                
                with col_btn:
                    if st.button("📥 Cargar Plantilla", use_container_width=True, type="secondary"):
                        tag_elegido = opciones_mostrar[seleccion_plantilla]
                        plantilla_a_cargar = catalogo_plantillas[tag_elegido]["esquema"]
                        
                        texto_plantilla = json.dumps(plantilla_a_cargar, indent=4, ensure_ascii=False)
                        st.session_state.json_editor = texto_plantilla
                        st.session_state[area_key] = texto_plantilla
                        st.rerun()
            else:
                st.warning("⚠️ No se encontró el archivo 'plantillas_equipos.json'. Ve a la Pestaña 3 para crear plantillas.")


            # --- AUTOCOMPLETADO CON IA ---
            st.divider()
            st.markdown("### 🤖 Autocompletado Inteligente")
            
            pdf_catalogo = st.file_uploader("Sube el PDF del equipo (Ej. Catálogo_DARSS.pdf)", type=['pdf'], key=f"up_{id_prod}")
            
            if pdf_catalogo and st.button("✨ Autocompletar con IA", key=f"btn_ia_{id_prod}", use_container_width=True):
                with st.spinner("Convirtiendo PDF a Markdown y extrayendo con Qwen..."):
                    texto_pdf_markdown = extraer_texto_pdf(pdf_catalogo)
                    
                    with st.expander("👀 Ver texto extraído por el PDF Parser (Debug)"):
                        if texto_pdf_markdown:
                            st.text(texto_pdf_markdown[:4000])
                        else:
                            st.error("El texto extraído es NULO.")
                    
                    if not texto_pdf_markdown or len(texto_pdf_markdown.strip()) < 50:
                        st.error("🚨 Error: El lector PDF no pudo extraer el texto.")
                    else:
                        json_base_para_ia = st.session_state.get(area_key, "{}")
                        
                        # Atrapamos las dos variables de tu nueva función
                        nuevo_json, error_ia = autocompletar_json_con_ia(texto_pdf_markdown, json_base_para_ia, modelo="qwen2.5:14b")
                        
                        if error_ia and nuevo_json:
                            # LA RED DE SEGURIDAD: Te mostramos el texto roto en el editor para que lo salves
                            st.warning(f"⚠️ **La IA hizo el trabajo, pero cometió un error de sintaxis:** {error_ia}")
                            st.info("Revisa el texto de abajo, corrige la coma o llave faltante, y guárdalo.")
                            st.session_state.json_editor = nuevo_json 
                            st.session_state[area_key] = nuevo_json
                            # Quitamos el st.rerun() aquí para que te deje ver las alertas amarillas
                            
                        elif nuevo_json:
                            # ÉXITO TOTAL
                            st.success("✅ Extracción perfecta.")
                            st.session_state.json_editor = nuevo_json 
                            st.session_state[area_key] = nuevo_json
                            st.rerun()
                        else:
                            st.error(f"💥 Fallo total en la extracción: {error_ia}")

           # --- ÁREA DE EDICIÓN Y GUARDADO ---
            st.divider()
            st.write("2. Edita y guarda los datos técnicos:")
            
            # El text_area ahora se alimenta EXCLUSIVAMENTE de su propia llave dinámica (area_key)
            json_editado = st.text_area("Formato JSON:", height=400, key=area_key)
            
            if st.button("💾 Guardar en Base de Datos", type="primary", key=f"save_{id_prod}", use_container_width=True):
                exito, mensaje = guardar_json_producto(id_prod, json_editado)
                
                if exito:
                    st.success(mensaje)
                    # Solo actualizamos el respaldo (json_editor), NO tocamos el area_key porque ya se actualizó sola al teclear
                    st.session_state.json_editor = json_editado
                else:
                    st.error(mensaje)