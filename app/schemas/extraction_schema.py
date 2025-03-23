from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class DocumentTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None

class DocumentTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        orm_mode = True

class SchemaCreate(BaseModel):
    document_type_id: int
    schema: Dict[str, Any]
    version: Optional[str] = "1.0"

class SchemaResponse(BaseModel):
    id: int
    document_type_id: int
    schema: Dict[str, Any]
    version: str
    created_at: datetime

    class Config:
        orm_mode = True

class ExtractionCreate(BaseModel):
    schema_id: int
    document_text: str

class ExtractionResponse(BaseModel):
    id: int
    schema_id: int
    document_text: str
    result: Dict[str, Any]
    extracted_at: datetime

    class Config:
        orm_mode = True