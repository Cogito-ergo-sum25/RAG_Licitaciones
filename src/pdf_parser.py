import fitz  # PyMuPDF
import os
import pytesseract
from PIL import Image
import io

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extraer_texto_pdf(archivo_entrada):
    """
    Extractor Nivel DIOS: Combina lectura directa de metadatos con OCR (Fuerza Bruta visual)
    para leer catálogos médicos escaneados o basados en imágenes.
    """
    try:
        # 1. Carga segura del archivo (ya sea desde Streamlit o ruta local)
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
        
        # 2. Barrido página por página
        for numero_pag in range(len(doc)):
            pagina = doc[numero_pag]
            texto_completo += f"\n\n{'='*20}\n[INICIO DE PÁGINA {numero_pag + 1}]\n{'='*20}\n\n"
            
            # Intento A: Lectura digital pura (Súper rápida)
            texto_pagina = pagina.get_text("text")
            
            # 3. EL CEREBRO: Si el texto extraído es muy corto, asumimos que es una IMAGEN/ESCÁNER
            if len(texto_pagina.strip()) < 50:
                print(f"⚠️ Página {numero_pag + 1} parece ser una imagen. Activando motor OCR...")
                texto_completo += "--- [TEXTO EXTRAÍDO POR VISIÓN ARTIFICIAL OCR] ---\n"
                
                # Renderizamos la página del PDF a una imagen de alta resolución (300 DPI)
                pix = pagina.get_pixmap(matrix=fitz.Matrix(2, 2)) # Zoom 2x para mejor lectura
                img_data = pix.tobytes("png")
                imagen_pillow = Image.open(io.BytesIO(img_data))
                
                # Tesseract lee la imagen. (lang='spa+eng' asume que puede venir en español o inglés)
                texto_ocr = pytesseract.image_to_string(imagen_pillow, lang='spa+eng')
                
                if texto_ocr.strip():
                    texto_completo += texto_ocr
                else:
                    texto_completo += "[ERROR OCR: No se pudo detectar texto en esta imagen]"
            else:
                # Si el PDF sí tenía texto digital normal, lo usamos.
                texto_completo += texto_pagina
                
            texto_completo += f"\n\n[FIN DE PÁGINA {numero_pag + 1}]\n\n"
            
        # Reseteamos el cursor de Streamlit por si acaso
        if hasattr(archivo_entrada, 'seek'):
            archivo_entrada.seek(0)
            
        return texto_completo
        
    except Exception as e:
        print(f"❌ Error crítico en PDF Parser Nivel DIOS: {e}")
        return f"Error en la extracción: {str(e)}"