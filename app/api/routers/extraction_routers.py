import os
import asyncio

from typing import List

from fastapi import (
    APIRouter,
    File, 
    UploadFile,
    HTTPException
    )

from langchain_community.document_loaders import PyPDFLoader, PDFPlumberLoader

from ...utils.utils import (
    get_file_size,
    save_file_to_temp,
    extract_text_with_ocr
)

from ...utils.utils import get_pdf_page_count, is_pdf_pure

extraction_router = APIRouter(
    prefix="/data-extraction",
    tags=["data-extraction"],
    responses={404: {"description": "Not found"}},
)

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB en bytes

# @extraction_router.post("/")
# async def data_extraction(files: List[UploadFile]):
#     results = []
#     for file in files:
#         temp_file_path = None
#         try:
#             # Validar tamaño del archivo
#             file_size = await get_file_size(file)
#             if file_size > MAX_FILE_SIZE:
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"El archivo {file.filename} excede el tamaño máximo permitido (200MB)."
#                 )

#             # Guardar archivo temporalmente sin cargarlo entero en memoria
#             temp_file_path = await save_file_to_temp(file)

#             # Verificar que la extensión sea PDF
#             if not file.filename.lower().endswith(".pdf"):
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"El archivo {file.filename} no es un PDF."
#                 )

#             # Obtener cantidad de páginas
#             num_pages = get_pdf_page_count(temp_file_path)

#             # Verificar si es un PDF 'puro' (con contenido textual)
#             pdf_pure = is_pdf_pure(temp_file_path)
#             if pdf_pure:
#                 results.append({
#                     "filename": file.filename,
#                     "size_bytes": file_size,
#                     "page_count": num_pages,
#                     "pdf_pure": True
#                 })
#             else:
#                 # PDF escaneado: se devuelve la info, indicando que es un PDF basado en imágenes.
#                 results.append({
#                     "filename": file.filename,
#                     "size_bytes": file_size,
#                     "page_count": num_pages,
#                     "pdf_pure": False,
#                     "message": "El PDF parece ser escaneado (sin contenido textual extraíble)."
#                 })

#         except HTTPException as e:
#             results.append({
#                 "filename": file.filename,
#                 "error": str(e.detail)
#             })
#         finally:
#             if temp_file_path and os.path.exists(temp_file_path):
#                 await asyncio.to_thread(os.remove, temp_file_path)

#     return {"results": results}

@extraction_router.post("/")
async def data_extraction(files: List[UploadFile]):
    results = []
    for file in files:
        temp_file_path = None
        try:
            # Validar tamaño del archivo
            file_size = await get_file_size(file)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"El archivo {file.filename} excede el tamaño máximo permitido (200MB)."
                )

            # Guardar archivo temporalmente sin cargarlo entero en memoria
            temp_file_path = await save_file_to_temp(file)

            # Verificar que la extensión sea PDF
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(
                    status_code=400,
                    detail=f"El archivo {file.filename} no es un PDF."
                )

            # Obtener cantidad de páginas
            num_pages = get_pdf_page_count(temp_file_path)

            # Verificar si es un PDF 'puro' (con contenido textual)
            pdf_pure = is_pdf_pure(temp_file_path)

            if pdf_pure:
                # Usar PyPDFLoader para PDFs con texto seleccionable
                loader = PyPDFLoader(temp_file_path)
                documents = await asyncio.to_thread(loader.load)  # Ejecutar en un hilo separado
                results.append({
                    "filename": file.filename,
                    "size_bytes": file_size,
                    "page_count": num_pages,
                    "pdf_pure": True,
                    "content": [doc.page_content for doc in documents]
                })
            else:
                # Para PDFs escaneados, usar OCR
                ocr_text = await extract_text_with_ocr(temp_file_path)
                if ocr_text.strip():  # Verificar si se extrajo texto
                    results.append({
                        "filename": file.filename,
                        "size_bytes": file_size,
                        "page_count": num_pages,
                        "pdf_pure": False,
                        "content": [ocr_text]
                    })
                else:
                    # Si OCR no encuentra texto, intentar con PDFPlumber por si tiene estructuras complejas
                    loader = PDFPlumberLoader(temp_file_path)
                    documents = await asyncio.to_thread(loader.load)
                    if documents and any(doc.page_content.strip() for doc in documents):
                        results.append({
                            "filename": file.filename,
                            "size_bytes": file_size,
                            "page_count": num_pages,
                            "pdf_pure": False,
                            "content": [doc.page_content for doc in documents],
                            "note": "Extraído con PDFPlumber (posible estructura compleja)"
                        })
                    else:
                        results.append({
                            "filename": file.filename,
                            "size_bytes": file_size,
                            "page_count": num_pages,
                            "pdf_pure": False,
                            "message": "No se pudo extraer contenido (PDF escaneado sin texto legible)"
                        })

        except HTTPException as e:
            results.append({
                "filename": file.filename,
                "error": str(e.detail)
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": f"Error inesperado: {str(e)}"
            })
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                await asyncio.to_thread(os.remove, temp_file_path)

    return {"results": results}