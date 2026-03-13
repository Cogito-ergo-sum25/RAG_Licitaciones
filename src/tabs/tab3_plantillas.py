import streamlit as st
import json
from src.db_client import obtener_todas_las_plantillas, guardar_plantilla_bd

def render_tab3():
    st.header("⚙️ Gestor de Reglas y Plantillas")
    st.markdown("Administra los esquemas JSON y las reglas de extracción que usa la IA (Guardado directamente en MySQL).")
    
    # Leemos directo de la Base de Datos
    plantillas = obtener_todas_las_plantillas()
    
    # 1. Selector en la parte superior
    st.subheader("📌 Seleccionar Categoría")
    opciones = ["➕ Crear Nueva Categoría"] + list(plantillas.keys())
    seleccion = st.selectbox("Elige una plantilla para editar o crea una nueva:", opciones)
    
    st.divider()
    
    # 2. Editor ocupando todo el ancho
    st.subheader("✏️ Editor de Plantilla")
    
    # Variables de estado inicial
    tag_actual = ""
    nombre_boton_actual = ""
    reglas_actuales = ""
    esquema_actual_str = "{}"
    
    # Si seleccionamos editar una existente, cargamos sus datos de la BD
    if seleccion != "➕ Crear Nueva Categoría":
        tag_actual = seleccion
        datos_plantilla = plantillas[seleccion]
        nombre_boton_actual = datos_plantilla.get("nombre_boton", "")
        reglas_actuales = datos_plantilla.get("reglas_especificas", "")
        esquema_actual_str = json.dumps(datos_plantilla.get("esquema", {}), indent=4, ensure_ascii=False)
        
    # Formulario de Edición
    with st.form("form_plantilla"):
        # Si es nueva, dejamos editar el Tag. Si ya existe, lo bloqueamos para no romper la llave primaria de MySQL.
        es_nueva = seleccion == "➕ Crear Nueva Categoría"
        nuevo_tag = st.text_input("Tag de la Categoría (ej. LAMPA, REFRI):", value=tag_actual, disabled=not es_nueva, help="Debe ser corto y en mayúsculas.")
        nuevo_nombre = st.text_input("Nombre Descriptivo (Para el botón):", value=nombre_boton_actual)
        
        st.markdown("**Reglas Específicas para la IA (Prompt):**")
        nuevas_reglas = st.text_area("Instrucciones trampa, conversiones o deducciones matemáticas:", value=reglas_actuales, height=250)
        
        st.markdown("**Esquema JSON Base:**")
        nuevo_esquema_str = st.text_area("Estructura de llaves (Usa null o 0):", value=esquema_actual_str, height=400)
        
        btn_guardar = st.form_submit_button("💾 Guardar en Base de Datos", type="primary", use_container_width=True)
        
        if btn_guardar:
            tag_final = nuevo_tag.strip().upper()
            if not tag_final:
                st.error("El Tag no puede estar vacío.")
            else:
                try:
                    # Validamos que el esquema sea un JSON correcto antes de enviarlo a MySQL
                    esquema_json = json.loads(nuevo_esquema_str)
                    
                    # Mandamos a guardar a MySQL usando nuestra función del db_client
                    exito, mensaje = guardar_plantilla_bd(
                        tag=tag_final,
                        nombre_boton=nuevo_nombre,
                        reglas_especificas=nuevas_reglas,
                        esquema_dict=esquema_json
                    )
                    
                    if exito:
                        st.success(f"¡Plantilla '{tag_final}' sincronizada con MySQL con éxito!")
                        st.rerun() # Recarga para actualizar la lista de arriba
                    else:
                        st.error(mensaje)
                        
                except json.JSONDecodeError as e:
                    st.error(f"❌ Error en el formato del JSON Base: {e}")