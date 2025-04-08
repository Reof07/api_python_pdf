import os
import asyncio
import pytesseract
from PIL import Image
from typing import Dict
from fastapi import UploadFile, HTTPException
from langchain_community.document_loaders import PyPDFLoader, PDFPlumberLoader

from ..utils.utils import get_pdf_page_count, is_pdf_pure, extract_text_with_ocr
from ..utils.utils import get_file_size, save_file_to_temp, preprocess_image
from ..core.tokenizers import tokenizer

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

class PDFExtractionService:
    @staticmethod
    async def extract_from_pdf(file: UploadFile) -> Dict:
        """
        Extrae contenido de un archivo PDF, ya sea puro o escaneado.
        Retorna un diccionario con los resultados, incluyendo el conteo de tokens.
        """
        temp_file_path = None
        try:
            # Validar tamaño del archivo
            file_size = await get_file_size(file)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"El archivo {file.filename} excede el tamaño máximo permitido (200MB)."
                )

            # Guardar archivo temporalmente
            temp_file_path = await save_file_to_temp(file)

            # Verificar que la extensión sea PDF
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(
                    status_code=400,
                    detail=f"El archivo {file.filename} no es un PDF."
                )

            # Obtener cantidad de páginas
            num_pages = get_pdf_page_count(temp_file_path)

            # Verificar si es un PDF 'puro' (con texto seleccionable)
            pdf_pure = is_pdf_pure(temp_file_path)

            if pdf_pure:
                # Usar PyPDFLoader para PDFs con texto seleccionable
                loader = PyPDFLoader(temp_file_path)
                documents = await asyncio.to_thread(loader.load)
                content = [doc.page_content for doc in documents]
            else:
                # Para PDFs escaneados, usar OCR
                ocr_text = await extract_text_with_ocr(temp_file_path)
                if ocr_text.strip():
                    content = [ocr_text]  # Lista con un solo elemento
                else:
                    # Si OCR no encuentra texto, intentar con PDFPlumber
                    loader = PDFPlumberLoader(temp_file_path)
                    documents = await asyncio.to_thread(loader.load)
                    if documents and any(doc.page_content.strip() for doc in documents):
                        content = [doc.page_content for doc in documents]
                    else:
                        return {
                            "filename": file.filename,
                            "size_bytes": file_size,
                            "page_count": num_pages,
                            "pdf_pure": False,
                            "message": "No se pudo extraer contenido (PDF escaneado sin texto legible)"
                        }

            # Calcular el número total de tokens en el contenido extraído
            total_tokens = sum(len(tokenizer.encode(chunk)) for chunk in content)

            # Devolver la respuesta incluyendo el conteo de tokens
            if pdf_pure:
                return {
                    "filename": file.filename,
                    "size_bytes": file_size,
                    "page_count": num_pages,
                    "pdf_pure": True,
                    "content": content,
                    "token_count": total_tokens
                }
            else:
                if "message" not in locals():  # Si no hay mensaje de error previo
                    return {
                        "filename": file.filename,
                        "size_bytes": file_size,
                        "page_count": num_pages,
                        "pdf_pure": False,
                        "content": content,
                        "token_count": total_tokens,
                        "note": "Extraído con OCR o PDFPlumber"
                    }

        except HTTPException as e:
            return {"filename": file.filename, "error": str(e.detail)}
        except Exception as e:
            return {"filename": file.filename, "error": f"Error inesperado: {str(e)}"}
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                await asyncio.to_thread(os.remove, temp_file_path)


class ImageExtractionService:
    @staticmethod
    async def extract_from_image(file: UploadFile) -> Dict:
        """
        Extrae contenido de un archivo de imagen (PNG, JPEG) usando OCR.
        Retorna un diccionario con los resultados, incluyendo el conteo de tokens.
        """
        temp_file_path = None
        try:
            # Validar tamaño del archivo
            file_size = await get_file_size(file)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"El archivo {file.filename} excede el tamaño máximo permitido (200MB)."
                )

            # Guardar archivo temporalmente
            temp_file_path = await save_file_to_temp(file)

            # Abrir imagen usando PIL
            try:
                image = Image.open(temp_file_path)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error al abrir la imagen: {str(e)}")

            # Preprocesar y extraer texto usando OCR
            processed_image = preprocess_image(image)
            ocr_text = pytesseract.image_to_string(processed_image, config="--oem 3 --psm 6")
            if not ocr_text.strip():
                return {
                    "filename": file.filename,
                    "size_bytes": file_size,
                    "message": "No se pudo extraer texto con OCR de la imagen."
                }

            # Calcular el número de tokens en el contenido extraído
            total_tokens = len(tokenizer.encode(ocr_text))

            return {
                "filename": file.filename,
                "size_bytes": file_size,
                "content": ocr_text,
                "token_count": total_tokens,
                "note": "Texto extraído de imagen con OCR"
            }
        except HTTPException as e:
            return {"filename": file.filename, "error": str(e.detail)}
        except Exception as e:
            return {"filename": file.filename, "error": f"Error inesperado: {str(e)}"}
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                await asyncio.to_thread(os.remove, temp_file_path)
