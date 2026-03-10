import fitz
import os

def extraer_texto_pdf(archivo_entrada):
    """
    Extrae texto crudo de un PDF de forma agresiva para evitar que el layout engine borre datos.
    """
    try:
        if hasattr(archivo_entrada, 'read'):
            archivo_entrada.seek(0)
            doc = fitz.open(stream=archivo_entrada.read(), filetype="pdf")
        elif isinstance(archivo_entrada, str):
            if not os.path.exists(archivo_entrada):
                print(f"❌ ERROR: No se encontró el archivo: {archivo_entrada}")
                return None
            doc = fitz.open(archivo_entrada)
        else:
            return None

        texto_completo = ""
        
        # Extracción pura y dura sin motor de layout para no perder textos flotantes
        for numero_pag in range(len(doc)):
            # get_text("text") asegura que lee todo el texto visible, sin importar el diseño
            texto_pagina = doc[numero_pag].get_text("text")
            
            texto_completo += f"\n\n{'='*20}\n[INICIO DE PÁGINA {numero_pag + 1}]\n{'='*20}\n\n"
            texto_completo += texto_pagina
            texto_completo += f"\n\n[FIN DE PÁGINA {numero_pag + 1}]\n\n"
            
        return texto_completo
        
    except Exception as e:
        print(f"❌ Error al extraer texto del PDF con PyMuPDF: {e}")
        return None