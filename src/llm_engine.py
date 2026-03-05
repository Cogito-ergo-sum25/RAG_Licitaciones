import ollama

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