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

def autocompletar_json_con_ia(texto_catalogo, json_plantilla, modelo="qwen2.5:14b"):
    print(f"Extrayendo datos con el modelo pesado {modelo}... Esto tomará su tiempo...\n")
    
    texto_seguro = texto_catalogo[:30000] 
    
    prompt = f"""
Analiza el siguiente catálogo médico y extrae la información técnica pura.

<CATALOGO>
{texto_seguro}
</CATALOGO>

INSTRUCCIONES DE EXTRACCIÓN (NIVEL PERITO):
1. Extrae los valores y llena la <PLANTILLA_BASE>.
2. IGNORA el texto de marketing ("la mejor calidad", "innovador"). Ve directo a los números, dimensiones, materiales y capacidades.
3. ESTANDARIZA: Si el catálogo dice "2050 mm", conviértelo lógicamente a centímetros si la plantilla lo pide en cm (ej. 205).
4. BOOLEANOS: Si el catálogo menciona una característica (ej. "incluye batería"), pon `true`. Si no la menciona en absoluto, pon `false` o `null` (NO asumas que la tiene).
5. TRADUCCIÓN: Traduce todo al español técnico de México (ej. "Stainless steel" -> "Acero inoxidable").
6. ACCESORIOS: Haz una lista exhaustiva de todos los accesorios enlistados. Si no hay lista, déjalo vacío [].

<PLANTILLA_BASE>
{json_plantilla}
</PLANTILLA_BASE>
"""
    
    try:
        import re
        respuesta = ollama.chat(model=modelo, messages=[
            {'role': 'system', 'content': 'Eres un extractor de datos JSON puro y estricto. Cero conversacional.'},
            {'role': 'user', 'content': prompt}
        ])
        
        texto_ia = respuesta['message']['content']
        match = re.search(r'\{.*\}', texto_ia, re.DOTALL)
        
        if match:
            texto_json_limpio = match.group(0)
            try:
                import json
                json_validado = json.loads(texto_json_limpio)
                return json.dumps(json_validado, indent=4, ensure_ascii=False)
            except json.JSONDecodeError:
                return None
        return None
    except Exception as e:
        print(f"❌ Error con Ollama: {e}")
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