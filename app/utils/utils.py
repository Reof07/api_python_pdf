import os
import tempfile
import concurrent.futures

import cv2
import numpy as np
from PIL import Image

from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract

from fastapi import UploadFile, HTTPException


CHUNK_SIZE = 1024 * 1024  # 1 MB por bloque


async def get_file_size(file: UploadFile) -> int:
    """
    Calcula el tamaño del archivo sin cargarlo completo en memoria.
    """
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    return size

async def save_file_to_temp(file: UploadFile) -> str:
    """
    Guarda el archivo en un archivo temporal en chunks para no consumir demasiada memoria.
    """
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        while True:
            chunk = await file.read(1024 * 1024)  # Lee de 1MB en 1MB
            if not chunk:
                break
            tmp.write(chunk)
        temp_path = tmp.name
    return temp_path

def get_pdf_page_count(temp_file_path: str) -> int:
    """
    Retorna la cantidad de páginas del PDF.
    """
    reader = PdfReader(temp_file_path)
    return len(reader.pages)

def is_pdf_pure(temp_file_path: str) -> bool:
    """
    Verifica si el PDF contiene texto.
    Si no encuentra texto en ninguna página, se asume que es un PDF basado en imágenes.
    """
    reader = PdfReader(temp_file_path)
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            return True
    return False


def preprocess_image(image: Image.Image) -> Image.Image:
    # Convertir PIL Image a array de numpy
    img = np.array(image)
    # Convertir a escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Aplicar un threshold adaptativo o global
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    # Convertir de vuelta a imagen PIL
    return Image.fromarray(thresh)


def ocr_page(page: Image.Image) -> str:
    processed_page = preprocess_image(page)
    return pytesseract.image_to_string(processed_page, config="--oem 3 --psm 6")


async def extract_text_with_ocr(pdf_path: str) -> str:
    try:
        pages = convert_from_path(pdf_path)
        text = ""
        # Usar ThreadPoolExecutor para procesamiento en paralelo
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(ocr_page, pages))
        text = "\n".join(results)
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en OCR: {str(e)}")


#version 2 (optimizado)
# async def extract_text_with_ocr(pdf_path: str) -> str:
#     """Extrae texto de un PDF escaneado usando OCR optimizado."""
#     try:
#         pages = convert_from_path(pdf_path)  # Convertir PDF a imágenes
#         text = ""
#         for page in pages:
#             # Preprocesar la imagen antes de OCR
#             processed_page = preprocess_image(page)
#             text += pytesseract.image_to_string(processed_page, config="--oem 3 --psm 6")
#         return text
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error en OCR: {str(e)}")

#version 1 (no optimizado)
# async def extract_text_with_ocr(pdf_path: str) -> str:
#     """Extrae texto de un PDF escaneado usando OCR."""
#     try:
#         pages = convert_from_path(pdf_path)  # Convertir PDF a imágenes
#         text = ""
#         for page in pages:
#             text += pytesseract.image_to_string(page)  # Extraer texto con OCR
#         return text
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error en OCR: {str(e)}")