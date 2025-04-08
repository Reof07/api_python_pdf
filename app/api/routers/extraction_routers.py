from typing import List

from fastapi import (
    APIRouter,
    File, 
    UploadFile,
    )

from ...service.pdf_reader import PDFExtractionService, ImageExtractionService, XMLExtractionService

extraction_router = APIRouter(
    prefix="/data-extraction",
    tags=["data-extraction"],
    responses={404: {"description": "Not found"}},
)

@extraction_router.post("/")
async def data_extraction(files: List[UploadFile]):
    """
    Procesa una lista de archivos PDF, imágenes (PNG, JPEG) y XML, 
    extrayendo su contenido usando el servicio correspondiente.
    """
    results = []
    for file in files:
        filename = file.filename.lower()
        if filename.endswith(".pdf"):
            result = await PDFExtractionService.extract_from_pdf(file)
        elif any(filename.endswith(ext) for ext in [".png", ".jpg", ".jpeg"]):
            result = await ImageExtractionService.extract_from_image(file)
        elif filename.endswith(".xml"):
            result = await XMLExtractionService.extract_from_xml(file)
        else:
            result = {
                "filename": file.filename,
                "error": "Tipo de archivo no soportado. Solo se permiten PDF, PNG, JPEG y XML."
            }
        results.append(result)
    return {"results": results}



@extraction_router.post("/xml")
async def extract_from_xml(file: UploadFile = File(...)):
    """
    Extrae contenido de un archivo XML usando UnstructuredXMLLoader.
    """
    # Validar tamaño del archivo que sea XML
    result = await XMLExtractionService.extract_from_xml(file)
    return result