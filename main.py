from src.excel_parser import procesar_licitacion_excel
from src.llm_engine import evaluar_con_ia

def iniciar_evaluador():
    print("=== SISTEMA EVALUADOR DE LICITACIONES ===\n")
    
    # 1. Leemos el Excel
    ruta_excel = "data/Propuestas.xlsx"
    diccionario_partidas = procesar_licitacion_excel(ruta_excel)
    
    if not diccionario_partidas:
        return

    # 2. Elegimos una partida específica para la prueba (Ej. El refrigerador mortuorio)
    nombre_partida_prueba = "I-REFRI-5317730207-0001"
    
    if nombre_partida_prueba not in diccionario_partidas:
        print(f"No se encontró la hoja '{nombre_partida_prueba}' en el Excel.")
        return
        
    texto_licitacion = diccionario_partidas[nombre_partida_prueba]
    
    # Recortamos a los primeros 1000 caracteres para la prueba rápida, 
    # para que la IA no se tarde mucho en este primer test.
    texto_licitacion_corto = texto_licitacion[:1000] 

    # 3. Simulamos lo que nos regresaría tu base de datos MySQL para el CEACA09
    json_ceaca09 = """
    {
      "marca": "CEABIS",
      "modelo": "CEACA09",
      "tipo": "Refrigerador para 2 cadáveres",
      "puertas": "2 de acceso lateral",
      "material_interior_exterior": "Acero inoxidable AISI-304",
      "rango_temperatura_celsius": {"min": -5, "max": 5},
      "capacidad_carga_por_bandeja_kg": 200,
      "gas_refrigerante": "Ecológico libre de CFC",
      "aislamiento": "Poliuretano libre de CFC"
    }
    """
    
    print("\n" + "="*50)
    print(f"EVALUANDO PARTIDA: {nombre_partida_prueba}")
    print("EQUIPO PROPUESTO: CEABIS CEACA09")
    print("="*50 + "\n")

    # 4. Mandamos todo a tu gráfica mediante Ollama
    # Asegúrate de tener llama3.1 o qwen2.5:14b instalado.
    resultado_ia = evaluar_con_ia(texto_licitacion_corto, json_ceaca09, modelo="llama3.1")
    
    if resultado_ia:
        print("\n=== DICTAMEN TÉCNICO DE LA IA ===\n")
        print(resultado_ia)

if __name__ == "__main__":
    iniciar_evaluador()