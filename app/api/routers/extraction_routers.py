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
from ...service.pdf_reader import PDFExtractionService

extraction_router = APIRouter(
    prefix="/data-extraction",
    tags=["data-extraction"],
    responses={404: {"description": "Not found"}},
)

@extraction_router.post("/")
async def data_extraction(files: List[UploadFile]):
    """
    Procesa una lista de archivos PDF y extrae su contenido usando el servicio de extracción.
    """
    results = []
    for file in files:
        result = await PDFExtractionService.extract_from_pdf(file)
        results.append(result)
    return {"results": results}