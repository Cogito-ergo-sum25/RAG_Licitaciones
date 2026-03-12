import streamlit as st
import json
import os

RUTA_PLANTILLAS = "plantillas_equipos.json"

def cargar_plantillas():
    if os.path.exists(RUTA_PLANTILLAS):
        with open(RUTA_PLANTILLAS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_plantillas(data):
    with open(RUTA_PLANTILLAS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def render_tab3():
    st.header("⚙️ Gestor de Reglas y Plantillas")
    st.markdown("Administra los esquemas JSON y las reglas de extracción (Prompt Engineering) que usa la IA para cada categoría de equipo.")
    
    plantillas = cargar_plantillas()
    
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
    
    # Si seleccionamos editar una existente, cargamos sus datos
    if seleccion != "➕ Crear Nueva Categoría":
        tag_actual = seleccion
        datos_plantilla = plantillas[seleccion]
        nombre_boton_actual = datos_plantilla.get("nombre_boton", "")
        reglas_actuales = datos_plantilla.get("reglas_especificas", "")
        esquema_actual_str = json.dumps(datos_plantilla.get("esquema", {}), indent=4, ensure_ascii=False)
        
    # Formulario de Edición
    with st.form("form_plantilla"):
        nuevo_tag = st.text_input("Tag de la Categoría (ej. LAMPA, REFRI):", value=tag_actual, help="Debe ser corto y en mayúsculas.")
        nuevo_nombre = st.text_input("Nombre Descriptivo:", value=nombre_boton_actual)
        
        st.markdown("**Reglas Específicas para la IA (Prompt):**")
        nuevas_reglas = st.text_area("Instrucciones trampa, conversiones o deducciones matemáticas:", value=reglas_actuales, height=250)
        
        st.markdown("**Esquema JSON Base:**")
        nuevo_esquema_str = st.text_area("Estructura de llaves (Usa null o 0):", value=esquema_actual_str, height=400)
        
        btn_guardar = st.form_submit_button("💾 Guardar Plantilla", type="primary", use_container_width=True)
        
        if btn_guardar:
            if not nuevo_tag.strip():
                st.error("El Tag no puede estar vacío.")
            else:
                try:
                    # Validamos que el esquema sea un JSON correcto antes de guardarlo
                    esquema_json = json.loads(nuevo_esquema_str)
                    
                    # Actualizamos el diccionario
                    plantillas[nuevo_tag.strip().upper()] = {
                        "nombre_boton": nuevo_nombre,
                        "reglas_especificas": nuevas_reglas,
                        "esquema": esquema_json
                    }
                    
                    guardar_plantillas(plantillas)
                    st.success(f"¡Plantilla '{nuevo_tag}' guardada con éxito!")
                    st.rerun() # Recarga para actualizar la lista de arriba
                except json.JSONDecodeError as e:
                    st.error(f"❌ Error en el formato del JSON Base: {e}")