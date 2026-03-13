import ollama
import json
import re

def evaluar_con_ia(texto_licitacion, json_equipo, modelo="qwen2.5:14b"):
    import ollama
    from src.db_client import obtener_configuracion_global
    
    print(f"Iniciando evaluación profunda con el modelo {modelo}...\n")
    
    # 1. Traemos las reglas del evaluador desde MySQL
    reglas_evaluador = obtener_configuracion_global('reglas_comunes_evaluador')
    
    # 2. Construimos el prompt final inyectando la licitación y el JSON
    prompt_maestro = f"""
    {reglas_evaluador}

    --- TEXTO DE LA LICITACIÓN ---
    {texto_licitacion}
    
    --- ESPECIFICACIONES DEL EQUIPO PROPUESTO (JSON) ---
    {json_equipo}
    """
    
    try:
        respuesta = ollama.chat(model=modelo, messages=[
            {
                'role': 'system',
                'content': 'Eres un auditor estricto. Respondes ÚNICAMENTE con una tabla Markdown. Citas los valores exactos del JSON. No inventas datos.'
            },
            {
                'role': 'user',
                'content': prompt_maestro
            }
        ])
        return respuesta['message']['content']
        
    except Exception as e:
        print(f"❌ Error al conectar con Ollama: {e}")
        return None

def autocompletar_json_con_ia(texto_catalogo, json_plantilla_str, modelo="qwen2.5:14b"):
    import json
    import re
    # Solo necesitamos las plantillas y el prompt maestro
    from src.db_client import obtener_todas_las_plantillas, obtener_configuracion_global
    
    print(f"Iniciando Extracción Técnica Pura con {modelo}...\n")
    
    texto_seguro = texto_catalogo[:40000] 
    
    try:
        plantilla_dict = json.loads(json_plantilla_str)
        tag_equipo = plantilla_dict.get("tag_licitacion", "OTRO")
    except:
        tag_equipo = "OTRO"

    # 1. REGLAS BASE OBLIGATORIAS (Jaladas directo de MySQL, sin inyecciones raras)
    reglas_comunes = obtener_configuracion_global(
        clave='reglas_comunes_extraccion', 
        valor_por_defecto="Extrae la información basándote en la <PLANTILLA_BASE>."
    )

    # 2. CARGAMOS LAS REGLAS ESPECÍFICAS DESDE MYSQL
    reglas_especificas = "<REGLAS_GENERALES>Extrae la información lo más apegado al texto posible.</REGLAS_GENERALES>"
    catalogo_plantillas = obtener_todas_las_plantillas()
    
    if tag_equipo in catalogo_plantillas:
        reglas_crud = catalogo_plantillas[tag_equipo].get("reglas_especificas", "").strip()
        if reglas_crud:
            reglas_especificas = f"<REGLAS_ESPECIALIZADAS>\n{reglas_crud}\n</REGLAS_ESPECIALIZADAS>"

    # 3. ARMAMOS EL PROMPT FINAL MAESTRO
    prompt = f"""
    Eres un Perito Biomédico especialista en dictaminar especificaciones técnicas de equipos médicos.
    
    <CATALOGO>
    {texto_seguro}
    </CATALOGO>
    
    {reglas_comunes}
    
    {reglas_especificas}

    <PLANTILLA_BASE>
    {json_plantilla_str}
    </PLANTILLA_BASE>
    
    Responde ÚNICAMENTE con el objeto JSON válido.
    """
    
    try:
        import ollama
        
        respuesta = ollama.chat(model=modelo, messages=[
            {'role': 'system', 'content': 'Eres un extractor de datos JSON puro. Cero conversacional. Responde SOLO con el código JSON.'},
            {'role': 'user', 'content': prompt}
        ])
        
        texto_ia = respuesta['message']['content']
        match = re.search(r'\{.*\}', texto_ia, re.DOTALL)
        
        if match:
            texto_json_limpio = match.group(0)
            
            # --- ESCUDOS DE SINTAXIS ---
            texto_json_limpio = re.sub(r'(\]|\}|"|true|false|null)\s*"referencias_paginas"', r'\1,\n    "referencias_paginas"', texto_json_limpio)
            texto_json_limpio = re.sub(r'\}\s*,\s*"referencias_paginas"', r',\n    "referencias_paginas"', texto_json_limpio)
            
            try:
                json_validado = json.loads(texto_json_limpio)
                return json.dumps(json_validado, indent=4, ensure_ascii=False), None
            except json.JSONDecodeError as e:
                print(f"❌ Error de sintaxis JSON: {e}")
                return texto_json_limpio, f"Error de sintaxis en la línea {e.lineno}: {e.msg}"
        return None, "No se encontró ningún formato JSON en la respuesta de la IA."
    except Exception as e:
        return None, f"Error de conexión con Ollama: {e}"
    
def obtener_top_3_equipos(texto_licitacion, diccionario_equipos, modelo="qwen2.5:14b"):
    print(f"Iniciando escaneo rápido de todo el inventario con {modelo}...\n")
    
    # Recortamos la licitación para el escaneo rápido (solo necesitamos las características principales)
    texto_corto = texto_licitacion[:4000]
    
    prompt = f"""
    Eres un director de ingeniería biomédica seleccionando el equipo ideal para una licitación.
    Analiza los requisitos de la licitación y compáralos contra nuestro catálogo disponible.
    
    <LICITACION>
    {texto_corto}
    </LICITACION>
    
    <CATALOGO_DISPONIBLE>
    {json.dumps(diccionario_equipos, ensure_ascii=False)}
    </CATALOGO_DISPONIBLE>
    
    INSTRUCCIONES ESTRICTAS:
    1. Selecciona los 3 equipos de nuestro catálogo que mejor cumplan con la licitación (o menos si hay pocas opciones).
    2. Devuelve tu respuesta en formato Markdown con el siguiente formato para cada equipo:
       - **[Marca] [Modelo]**: [Porcentaje estimado de compatibilidad]%
       - **Por qué:** [Explicación de 2 líneas de sus puntos fuertes y qué le falta]
    3. NO uses formato JSON. Sé directo y analítico.
    """
    
    try:
        respuesta = ollama.chat(model=modelo, messages=[
            {
                'role': 'system',
                'content': 'Eres un recomendador experto. Sé conciso y analítico.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ])
        
        return respuesta['message']['content']
        
    except Exception as e:
        print(f"❌ Error al conectar con Ollama en el ranking: {e}")
        return None
    
def evaluar_cumplimiento_ia(texto_imss, json_equipo_str, modelo="qwen2.5:14b"):
    import json
    import re
    
    prompt = f"""
    Eres un Perito Biomédico dictaminador evaluando si un equipo médico cumple con los requisitos técnicos de una licitación pública.
    
    <REQUISITOS_LICITACION_IMSS>
    {texto_imss}
    </REQUISITOS_LICITACION_IMSS>
    
    <ESPECIFICACIONES_DEL_EQUIPO_OFERTADO>
    {json_equipo_str}
    </ESPECIFICACIONES_DEL_EQUIPO_OFERTADO>
    
    INSTRUCCIONES DE EVALUACIÓN:
    1. Compara cada punto del texto del IMSS contra el JSON del equipo.
    2. Usa LÓGICA CLÍNICA Y MATEMÁTICA ESTRICTA:
       - Si el IMSS pide "Mínimo 100,000 luxes" y el equipo tiene 240,000 -> 🟢 CUMPLE.
       - Si el IMSS pide "Microprocesador" y el equipo dice `false` -> 🔴 NO CUMPLE.
       - Si el IMSS pide "Filtro UV" y el equipo no lo menciona (null/ausente) -> 🟡 SIN INFORMACIÓN.
    3. Calcula un "score" de cumplimiento del 0 al 100 basado en cuántos puntos cumple.

    FORMATO DE RESPUESTA OBLIGATORIO (Devuelve SOLO JSON válido):
    {{
        "score_cumplimiento": 100,
        "veredicto_general": "CUMPLE TOTALMENTE",
        "puntos_evaluados": [
            {{
                "requisito_imss": "Intensidad luminosa mínima de 100,000 luxes",
                "especificacion_equipo": "240,000 luxes",
                "semaforo": "🟢",
                "justificacion": "Supera el requerimiento mínimo."
            }}
        ]
    }}
    """
    
    try:
        import ollama
        respuesta = ollama.chat(model=modelo, messages=[
            {'role': 'system', 'content': 'Eres un evaluador técnico estricto. Responde SOLO con JSON válido.'},
            {'role': 'user', 'content': prompt}
        ])
        
        texto_ia = respuesta['message']['content']
        match = re.search(r'\{.*\}', texto_ia, re.DOTALL)
        
        if match:
            try:
                json_validado = json.loads(match.group(0))
                return json_validado
            except json.JSONDecodeError as e:
                print(f"❌ Error en JSON del evaluador: {e}")
                return None
        return None
    except Exception as e:
        print(f"❌ Error conectando con Ollama en evaluador: {e}")
        return None
    
def escaner_rapido_score(texto_requisitos, json_equipo_str, modelo="qwen2.5:14b"):
    import json
    import re
    
    prompt = f"""
    Eres un algoritmo matemático de filtrado técnico. Tu único objetivo es calcular el porcentaje de compatibilidad entre los requisitos de una licitación y las especificaciones de un equipo.
    
    REQUISITOS DE LA LICITACIÓN:
    {texto_requisitos}
    
    ESPECIFICACIONES DEL EQUIPO:
    {json_equipo_str}
    
    REGLAS DE LA FÓRMULA:
    1. Extrae mentalmente los puntos clave del requisito (ej. capacidad, material, dimensiones).
    2. Cruza cada punto contra el equipo. Usa lógica matemática estricta (si piden 200kg y tiene 220kg, sí cumple).
    3. Calcula un "score_compatibilidad" de 0 a 100. (100 = cumple todo o lo supera, 50 = le faltan la mitad de cosas, 0 = es un equipo totalmente distinto).
    
    RESPONDE ÚNICA Y ESTRICTAMENTE CON ESTE FORMATO JSON:
    {{
        "score_compatibilidad": 85,
        "motivo_principal": "Cumple en capacidad y material, pero difiere ligeramente en dimensiones.",
        "alertas_rojas": ["No cuenta con batería de respaldo", "Voltaje incompatible"]
    }}
    """
    
    try:
        import ollama
        respuesta = ollama.chat(model=modelo, messages=[
            {'role': 'system', 'content': 'Solo devuelves JSON válido sin texto extra.'},
            {'role': 'user', 'content': prompt}
        ])
        
        texto_ia = respuesta['message']['content']
        match = re.search(r'\{.*\}', texto_ia, re.DOTALL)
        
        if match:
            return json.loads(match.group(0))
        return None
    except Exception as e:
        print(f"❌ Error en escáner rápido: {e}")
        return None