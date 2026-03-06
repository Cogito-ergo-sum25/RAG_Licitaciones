import ollama
import json
import re 

def evaluar_con_ia(texto_licitacion, json_equipo, modelo="qwen2.5:14b"):
    print(f"Iniciando evaluación profunda con el modelo {modelo}...\n")
    
    prompt_maestro = f"""
    Eres un perito dictaminador biomédico evaluando el cumplimiento técnico de un equipo médico para una licitación pública.
    Tu trabajo es comparar los requisitos de la licitación contra el JSON de especificaciones del equipo propuesto.
    
    REGLAS MATEMÁTICAS Y DE AUDITORÍA (INQUEBRANTABLES):
    1. PROHIBIDO INFERIR: Si un dato no está en el JSON, o su valor es 0, null, o vacío [], NO asumas que lo cumple. Repórtalo como "Sin Información".
    2. CONVERSIÓN DE UNIDADES: Antes de evaluar, unifica las unidades. Si la licitación pide cm y el JSON está en mm, conviértelo mentalmente (ej. 2050 mm = 205 cm).
    3. RANGOS Y TOLERANCIAS: Si la licitación pide "210 cm +/- 10 cm", el rango aceptable es de 200 cm a 220 cm. Calcula esto antes de dar tu fallo.
    
    CÓDIGO DE EVALUACIÓN ESTRICTO (Usa exactamente estos emojis y categorías):
    ⚪ [CUMPLE]: El equipo cumple exactamente con el requerimiento o cae perfectamente dentro del rango solicitado.
    🟢 [SUPERA]: El equipo ofrece una especificación superior o un rango más amplio que el solicitado (ej. piden 20°, ofrece 46°).
    🔵 [SIMILAR]: El equipo utiliza una tecnología distinta pero funcionalmente equivalente para el mismo propósito clínico.
    🟡 [SIN INFORMACIÓN]: El catálogo (JSON) no menciona este punto, el valor es 0, false (cuando se pedía la característica) o está vacío. 
    🔴 [NO CUMPLE]: La especificación del equipo es inferior, contradice o no alcanza el mínimo requerido.
    
    INSTRUCCIONES DE FORMATO (ESTRICTAS):
    - Tu respuesta DEBE ser EXCLUSIVAMENTE una tabla en formato Markdown con dos columnas.
    - Columna 1: "Requisito Original" (Copia aquí el texto del punto, ej. 1.1, 1.2...).
    - Columna 2: "Dictamen Técnico" (Pon aquí el emoji, tu veredicto y la justificación citando el JSON).
    - Ignora los renglones que digan "Referencia Catálogo/Manual:".
    
    EJEMPLO DE SALIDA ESPERADA:
    | Requisito Original | Dictamen Técnico |
    |---|---|
    | 1.1.- Mesa quirúrgica electrohidráulica. | 🟢 [CUMPLE]: El JSON indica 'tipo_equipo': 'Mesa Quirúrgica Electrohidráulica'. |
    
    --- TEXTO DE LA LICITACIÓN ---
    {texto_licitacion}
    
    --- ESPECIFICACIONES DEL EQUIPO PROPUESTO (JSON) ---
    {json_equipo}
    """
    
    try:
        respuesta = ollama.chat(model=modelo, messages=[
            {
                'role': 'system',
                'content': 'Eres un auditor estricto, matemático y analítico. No inventas datos ni asumes características que no estén escritas en el JSON.'
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
    
    # Un límite de 30,000 caracteres (unas 15 páginas) es el punto dulce para Qwen 2.5
    texto_seguro = texto_catalogo[:30000] 
    
    # Fíjate cómo el texto está encerrado en XML tags y las instrucciones van al final
    prompt = f"""
Analiza el siguiente documento y extrae la información técnica.

<DOCUMENTO>
{texto_seguro}
</DOCUMENTO>

INSTRUCCIONES ESTRICTAS:
1. Extrae los valores técnicos del <DOCUMENTO> y úsalos para llenar esta <PLANTILLA_BASE>.
2. AGREGA nuevas llaves (keys) al JSON si encuentras datos relevantes (accesorios, voltajes, dimensiones, materiales).
3. TRADUCE AL ESPAÑOL TODAS LAS LLAVES NUEVAS Y SUS VALORES. Aunque el catálogo esté en inglés u otro idioma, las llaves y el contenido del JSON deben generarse estrictamente en español (ej. usa "dimensiones_cabezal_cm" en lugar de "head_dimensions").
4. Tu respuesta DEBE ser ÚNICAMENTE un objeto JSON válido. No escribas saludos, ni resúmenes, ni viñetas.

<PLANTILLA_BASE>
{json_plantilla}
</PLANTILLA_BASE>
"""
    
    try:
        # Aquí le quitamos el format='json' porque a veces buguea a Qwen.
        # Mejor confiamos en nuestro extractor Regex de abajo.
        respuesta = ollama.chat(model=modelo, messages=[
            {
                'role': 'system',
                'content': 'Eres una API automatizada. Recibes texto y devuelves exclusivamente código JSON puro que empieza con { y termina con }. Cero texto conversacional.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ])
        
        texto_ia = respuesta['message']['content']
        
        # --- EL EXTRACTOR NINJA (REGEX) ---
        # Busca todo lo que esté entre el primer "{" y el último "}"
        match = re.search(r'\{.*\}', texto_ia, re.DOTALL)
        
        if match:
            texto_json_limpio = match.group(0)
            try:
                # Validamos que sea un JSON real
                json_validado = json.loads(texto_json_limpio)
                return json.dumps(json_validado, indent=4, ensure_ascii=False)
            except json.JSONDecodeError:
                print("❌ La IA generó un JSON roto.")
                print("Respuesta cruda:", texto_json_limpio)
                return None
        else:
            print("❌ No se encontró ningún formato JSON en la respuesta de la IA.")
            print("Respuesta cruda:", texto_ia)
            return None
            
    except Exception as e:
        print(f"❌ Error al conectar con Ollama: {e}")
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