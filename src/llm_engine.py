import ollama
import json
import re 

def evaluar_con_ia(texto_licitacion, json_equipo, modelo="llama3.1"):
    print(f"Iniciando evaluación con el modelo {modelo} en tu RX 7600 XT...\n")
    
    # El "System Prompt" es la regla de oro. Aquí le decimos a la IA cómo comportarse.
    prompt_maestro = f"""
    Eres un ingeniero biomédico experto en licitaciones públicas de equipo médico.
    Tu tarea es comparar los requisitos de la licitación contra las especificaciones técnicas de un equipo en formato JSON.
    
    REGLAS ESTRICTAS:
    1. Evalúa punto por punto el texto de la licitación.
    2. Usa ESTRICTAMENTE este código de colores para cada punto:
       🟢 [Verde] Cumple. (Si el JSON lo supera o lo cumple exactamente)
       🟡 [Amarillo] Parcial. (Si el JSON no lo menciona o falta un documento)
       🔴 [Rojo] No cumple. (Si el JSON contradice el requisito)
       🔵 [Azul] Similar. (Si la tecnología es equivalente)
    3. Justifica brevemente tu respuesta basándote SOLO en los datos del JSON. No inventes características que no estén en el JSON.
    4. Ignora los renglones que digan "Referencia Catálogo/Manual:"
    
    --- TEXTO DE LA LICITACIÓN ---
    {texto_licitacion}
    
    --- ESPECIFICACIONES DEL EQUIPO (JSON) ---
    {json_equipo}
    """
    
    try:
        # Llamamos a Ollama localmente
        respuesta = ollama.chat(model=modelo, messages=[
            {
                'role': 'user',
                'content': prompt_maestro
            }
        ])
        return respuesta['message']['content']
        
    except Exception as e:
        print(f"❌ Error al conectar con Ollama: {e}")
        print("¿Asegúrate de que Ollama esté corriendo en segundo plano y el modelo esté descargado!")
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