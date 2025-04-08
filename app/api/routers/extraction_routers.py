from typing import List

from fastapi import (
    APIRouter,
    File, 
    UploadFile,
    )

from ...service.pdf_reader import PDFExtractionService, ImageExtractionService

extraction_router = APIRouter(
    prefix="/data-extraction",
    tags=["data-extraction"],
    responses={404: {"description": "Not found"}},
)


@extraction_router.post("/")
async def data_extraction(files: List[UploadFile]):
    """
    Procesa una lista de archivos PDF y/o imágenes (PNG, JPEG) y extrae su contenido usando el servicio de extracción correspondiente.
    """
    results = []
    for file in files:
        filename = file.filename.lower()
        # Si el archivo es PDF, usar el servicio PDF existente
        if filename.endswith(".pdf"):
            result = await PDFExtractionService.extract_from_pdf(file)
        # Si es imagen (png, jpg, jpeg)
        elif any(filename.endswith(ext) for ext in [".png", ".jpg", ".jpeg"]):
            result = await ImageExtractionService.extract_from_image(file)
        else:
            result = {
                "filename": file.filename,
                "error": "Tipo de archivo no soportado. Solo se permiten PDF, PNG y JPEG."
            }
        results.append(result)
    return {"results": results}