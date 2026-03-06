import pdfplumber
import os

def extraer_texto_pdf(archivo_entrada):
    """
    Extrae todo el texto de un archivo PDF.
    Acepta tanto una ruta de texto local como un archivo subido por Streamlit en RAM.
    """
    if isinstance(archivo_entrada, str):
        if not os.path.exists(archivo_entrada):
            print(f"❌ ERROR: No se encontró el archivo en la ruta {archivo_entrada}")
            return None

    texto_completo = ""
    
    try:
        # Abrimos el PDF con pdfplumber
        with pdfplumber.open(archivo_entrada) as pdf:
            # Recorremos todas las páginas
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"
                
        return texto_completo
        
    except Exception as e:
        print(f"❌ Error al extraer texto del PDF: {e}")
        return None

if __name__ == "__main__":
    # Prueba rápida local
    # Asegúrate de tener un PDF de prueba en esta ruta si lo corres desde la terminal
    ruta_prueba = "data/anexos_prueba/B-LAMPA-5315620046-0003.pdf"
    
    texto = extraer_texto_pdf(ruta_prueba)
    if texto:
        print("✅ ¡Extracción exitosa!")
        print("="*50)
        print(texto[:1000]) # Imprime los primeros 1000 caracteres
        print("="*50)