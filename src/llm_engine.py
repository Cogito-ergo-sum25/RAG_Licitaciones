import ollama
import json
import re

def evaluar_con_ia(texto_licitacion, json_equipo, modelo="qwen2.5:14b"):
    print(f"Iniciando evaluación profunda con el modelo {modelo}...\n")
    
    prompt_maestro = f"""
    Eres un perito dictaminador biomédico evaluando el cumplimiento técnico de un equipo médico para una licitación del IMSS.
    Compara los requisitos de la licitación contra el JSON del equipo.
    
    REGLAS DE EVALUACIÓN Y COLORES (INQUEBRANTABLES):
    🟢 [CUMPLE / SUPERA]: El equipo cumple exactamente o SUPERA el requerimiento. 
        - Ejemplo: Piden 185 kg, el JSON dice 450 kg -> 🟢 [CUMPLE / SUPERA].
        - Ejemplo: Piden 210 cm +/- 10 cm, el JSON dice 205 cm -> 🟢 [CUMPLE / SUPERA].
    🔵 [SIMILAR]: El equipo no cumple exactamente al 100%, pero el rango o tecnología es similar y funcionalmente aceptable.
        - Ejemplo: Piden diámetro de 7 a 30 cm, el JSON dice de 12 a 30 cm -> 🔵 [SIMILAR].
    🟡 [SIN INFORMACIÓN]: El catálogo/JSON no menciona este punto, está vacío [], o el valor es 0. PROHIBIDO INFERIR.
        - Ejemplo: Piden manuales y el JSON no dice nada -> 🟡 [SIN INFORMACIÓN].
        - Ejemplo: Piden accesorios y el array está vacío -> 🟡 [SIN INFORMACIÓN].
    🔴 [NO CUMPLE]: La especificación del equipo es inferior, contradice o no alcanza el requerimiento.
        - Ejemplo: Piden tablero giratorio y el JSON dice false -> 🔴 [NO CUMPLE].

    FORMATO DE SALIDA (ESTRICTO MARKDOWN TABLE):
    | Requisito Original | Dictamen Técnico |
    |---|---|
    | 1.1.- Texto del requisito | 🟢 [CUMPLE / SUPERA]: Justificación citando el JSON exacto. |
    | 1.2.- Texto del requisito | 🟡 [SIN INFORMACIÓN]: El JSON no especifica este dato. |

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
    print(f"Iniciando Extracción Nivel Perito Enrutada con {modelo}...\n")
    
    texto_seguro = texto_catalogo[:40000] 
    
    try:
        plantilla_dict = json.loads(json_plantilla_str)
        tag_equipo = plantilla_dict.get("tag_licitacion", "OTRO")
    except:
        tag_equipo = "OTRO"

    # 2. REGLAS BASE OBLIGATORIAS PARA TODOS LOS EQUIPOS
    reglas_comunes = """
    INSTRUCCIONES DE EXTRACCIÓN (NIVEL PERITO ESTRICTO):
    1. Extrae los valores y llena la <PLANTILLA_BASE>.
    2. REGLA DE BOOLEANOS: Si el catálogo NO menciona una característica en absoluto, pon `false` o `null`. ¡PROHIBIDO ASUMIR!
    3. TRADUCCIÓN: Traduce al español clínico de México (Ej: "Stainless steel" -> "Acero Inoxidable").
    4. ESTRUCTURA ESTRICTA: ESTÁ ESTRICTAMENTE PROHIBIDO INVENTAR LLAVES NUEVAS. Utiliza ÚNICAMENTE las llaves exactas que vienen en la <PLANTILLA_BASE>. Si no hay datos, usa null o 0, pero respeta la estructura original.
    
    <MATRIZ_DE_REFERENCIAS>
    - Siempre al final de tu respuesta, agrega una llave obligatoria llamada "referencias_paginas".
    - ¡REGLA DE SINTAXIS ESTRICTA!: "referencias_paginas" DEBE ser un objeto JSON anidado que mapee CADA UNA de las variables, NO un string y NO puede estar vacío.
    - Ejemplo del formato EXACTO que debes usar:
      "referencias_paginas": {{
          "potencia_maxima_watts": "Página 1",
          "intensidad_luminosa_luxes": "Página 2",
          "control_por_microprocesador": "No encontrado"
      }}
    - Mapea todas las llaves. Si encontraste el dato, pon la "Página X". Si NO lo encontraste, pon "No encontrado".
    </MATRIZ_DE_REFERENCIAS>
    """

    # 3. REGLAS ESPECÍFICAS (EL CEREBRO DE CADA EQUIPO)
    reglas_especificas = ""
    
    if tag_equipo == "MESAS":
        reglas_especificas = """
        <REGLAS_ESPECIALIZADAS_PARA_MESAS>
        CASO A: Conversión de Unidades y Rangos Matemáticos
        - Si el diagrama dice: "Height 680 mm - 1120 mm". Convierte a cm: "rango_elevacion_descenso_cm": {{"min": 68, "max": 112}}.
        - Si la tabla dice: "Table Height 680mm ± 20mm" y "Height Adjustment Range ≥250mm". SUMA EL RANGO: "rango_elevacion_descenso_cm": {{"min": 68, "max": 93}} (Porque 68 + 25 = 93).
        - Si el texto dice: "Trendelenburg ≥25°" y "Lateral Tilt 20° ± 2°". Ignora los símbolos matemáticos: "grados_trendelenburg": 25, "grados_inclinacion_lateral": 20.

        CASO B: Anti-Confusión de Medidas
        - Si el texto dice: "12.2 pulgadas (31 cm) Deslizamiento Longitudinal". Tu deducción es: "acceso_arco_en_c_desplazamiento_longitudinal_cm": 31.
        - ¡REGLA DE ORO!: NUNCA asignes el valor de "deslizamiento" (slide) a las llaves de "elevación/descenso" (height).

        CASO C: Mecánico vs Eléctrico
        - Si el texto dice "manual mechanic operating table" o "bomba de pie". Deduce: "control_por_microprocesador": false, "sistema_emergencia_bombeo_hidraulico_manual": true. Y pon todo lo eléctrico (batería, panel) en false.
        
        CASO D: Booleanos Especiales
        - "costura soldada" o "anti-decubitus" significa que "cojines_conductivos_antiestaticos_sin_costuras": true.
        - "Double-locking levers" significa que "sistema_frenos_pivotes_anclaje": true.
        </REGLAS_ESPECIALIZADAS_PARA_MESAS>
        """
        
    elif tag_equipo == "LAMPA":
        reglas_especificas = """
        <REGLAS_ESPECIALIZADAS_PARA_LAMPARAS>
        CASO A: Grandes Números (Sintaxis Estricta)
        - Si el texto dice "160,000 Lux" o "160k Lux". El número DEBE ir sin comas: "intensidad_luminosa_luxes": 160000.
        - Si el texto dice "50,000 h minimum". El número va sin comas: "vida_util_horas": 50000.
        
        CASO B: Tablas de Luxes por Distancia
        - Si el texto muestra una tabla (ej. 20000 a 30cm, 7000 a 50cm). Escoge SIEMPRE el valor MÁXIMO de intensidad: "intensidad_luminosa_luxes": 20000.

        CASO C: Conversión a Centímetros
        - Si el texto dice: "Light field diameter (d10): 150 - 300 mm". Convierte estrictamente a CENTÍMETROS: "diametro_campo_iluminacion_cm": {{"min": 15, "max": 30}}.
        - Si te da varias opciones de brazo "Flexible 65 cm, 100 cm, 123 cm". Selecciona EL MÁS LARGO en un solo número: "longitud_brazo_flexible_cm": 123.

        CASO D: Quirúrgica vs Fototerapia
        - Si el catálogo es de una lámpara de examinación o quirófano normal (ej. "Surgical Light").
        - ¡REGLA DE ORO!: Pon en 0 o null todo lo de fototerapia ("fototerapia_longitud_onda_nm": null, "fototerapia_irradiacion...": 0). No inventes datos.

        CASO E: LED vs Halógeno
        - Si el texto dice "Halogen bulb", la "tecnologia_iluminacion" debe ser "Halógeno" y la "cantidad_minima_leds" debe ser obligatoriamente null o 0.
        </REGLAS_ESPECIALIZADAS_PARA_LAMPARAS>
        """
        
    elif tag_equipo == "REFRI":
        reglas_especificas = """
        <REGLAS_ESPECIALIZADAS_PARA_REFRIGERADORES>
        1. TEMPERATURAS: Extrae siempre el rango en grados Celsius.
        2. MATERIALES: Especifica claramente el tipo de acero inoxidable (ej. AISI-304) si se menciona.
        </REGLAS_ESPECIALIZADAS_PARA_REFRIGERADORES>
        """

    else:
        reglas_especificas = "<REGLAS_GENERALES>Extrae la información lo más apegado al texto posible.</REGLAS_GENERALES>"

    # 4. ARMAMOS EL PROMPT FINAL MAESTRO
    prompt = f"""
    Eres un Perito Biomédico especialista en dictaminar equipos médicos.
    
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
            
            # --- ESCUDO ANTI-ERRORES DE SINTAXIS (LA COMA SALVAVIDAS) ---
            texto_json_limpio = re.sub(r'(\]|\}|"|true|false|null)\s*"referencias_paginas"', r'\1,\n    "referencias_paginas"', texto_json_limpio)
            
            try:
                json_validado = json.loads(texto_json_limpio)
                return json.dumps(json_validado, indent=4, ensure_ascii=False)
            except json.JSONDecodeError as e:
                print(f"❌ La IA no devolvió un JSON válido. Error: {e}")
                print(f"Texto problemático:\n{texto_json_limpio}")
                return None
        return None
    except Exception as e:
        print(f"❌ Error con Ollama en autocompletar: {e}")
        return None
    
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