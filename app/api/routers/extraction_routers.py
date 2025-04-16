from typing import List

from charset_normalizer import from_bytes

from fastapi import (
    APIRouter,
    File, 
    UploadFile,
    HTTPException,
    )

from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
import pandas as pd

from ...service.pdf_reader import (
    PDFExtractionService, 
    ImageExtractionService, 
    XMLExtractionService,
    CSVExtractionService,
)

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
    try:
        excel_io, filename = await XMLExtractionService.extract_from_xml(file)
    except HTTPException as e:
        raise e
    return StreamingResponse(
        excel_io,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@extraction_router.post("/csv")
async def extract_from_csv(file: UploadFile = File(...)):
    
    
    result = await CSVExtractionService.extract_from_csv(file)
    
    if "error" in result:
        return JSONResponse(
            status_code=400 if "máximo permitido" in result["error"] else 500,
            content=result
        )
        
    return FileResponse(
        path=result["excel_path"],
        filename="convertido.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
