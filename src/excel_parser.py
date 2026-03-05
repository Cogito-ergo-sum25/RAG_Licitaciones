import pandas as pd
import os

def procesar_licitacion_excel(archivo_entrada):
    # Validamos si es una ruta de texto (para cuando lo corres en terminal)
    if isinstance(archivo_entrada, str):
        print(f"Abriendo el mega-archivo desde ruta: {archivo_entrada}...\n")
        if not os.path.exists(archivo_entrada):
            print(f"❌ ERROR: No se encontró el archivo en la ruta {archivo_entrada}")
            return None
    else:
        # Si no es texto, asumimos que viene de Streamlit (UploadedFile)
        print("Abriendo archivo directamente desde la memoria de Streamlit...\n")

    diccionario_partidas = {}

    try:
        # Cargamos el archivo de Excel completo
        # Pandas es tan listo que acepta la ruta de texto o el objeto en RAM de Streamlit
        archivo_excel = pd.ExcelFile(archivo_entrada)
        
        # Iteramos por cada pestaña (hoja) del Excel
        for nombre_hoja in archivo_excel.sheet_names:
            
            # Leemos la hoja
            df = pd.read_excel(archivo_excel, sheet_name=nombre_hoja, header=None)
            
            # Extraemos SOLO la Columna A (índice 0) y quitamos celdas vacías (NaN)
            columna_a = df.iloc[:, 0].dropna()
            
            # Convertimos esa columna a texto y la unimos con saltos de línea
            texto_partida = "\n".join(columna_a.astype(str).tolist())
            
            # --- LIMPIEZA DEL ENCABEZADO (RUIDO) ---
            marcador_inicio = "1.- DESCRIPCIÓN:"
            indice_inicio = texto_partida.find(marcador_inicio)
            
            if indice_inicio != -1:
                # Recortamos el texto para que empiece exactamente desde el marcador
                texto_partida = texto_partida[indice_inicio:]
            # --------------------------------------
            
            # Guardamos el texto limpio en nuestro diccionario
            diccionario_partidas[nombre_hoja] = texto_partida
            
        return diccionario_partidas

    except Exception as e:
        print(f"❌ Error al leer el Excel: {e}")
        return None

if __name__ == "__main__":
    # Prueba local
    ruta = "data/Propuestas.xlsx" 
    partidas = procesar_licitacion_excel(ruta)
    if partidas:
        print("\n✅ ¡Extracción exitosa!\n")