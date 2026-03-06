import fitz  # PyMuPDF
import pymupdf4llm
import os

def extraer_texto_pdf(archivo_entrada):
    """
    Extrae todo el texto de un archivo PDF y lo convierte a MARKDOWN.
    Acepta tanto una ruta local (str) como un archivo subido por Streamlit en RAM.
    """
    try:
        # Si el archivo viene de Streamlit (UploadedFile)
        if hasattr(archivo_entrada, 'read'):
            # Para leerlo en RAM hay que volver al inicio del archivo por si ya se leyó antes
            archivo_entrada.seek(0)
            doc = fitz.open(stream=archivo_entrada.read(), filetype="pdf")
            
        # Si es una ruta de texto local (para pruebas en terminal)
        elif isinstance(archivo_entrada, str):
            if not os.path.exists(archivo_entrada):
                print(f"❌ ERROR: No se encontró el archivo en la ruta {archivo_entrada}")
                return None
            doc = fitz.open(archivo_entrada)
            
        else:
            print("❌ ERROR: Formato de archivo no soportado.")
            return None

        # Convertimos a Markdown respetando tablas
        texto_markdown = pymupdf4llm.to_markdown(doc)
        return texto_markdown
        
    except Exception as e:
        print(f"❌ Error al extraer texto del PDF con PyMuPDF: {e}")
        return None

if __name__ == "__main__":
    # Prueba rápida local
    ruta_prueba = "data/anexos_prueba/B-LAMPA-5315620046-0003.pdf"
    
    texto = extraer_texto_pdf(ruta_prueba)
    if texto:
        print("✅ ¡Extracción exitosa a Markdown!")
        print("="*50)
        print(texto[:1000]) 
        print("="*50)