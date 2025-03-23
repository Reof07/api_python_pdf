from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base



class DocumentType(Base):
    __tablename__ = "document_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now())
    
    # Relación 1:N con Schemas
    schemas = relationship("Schema", back_populates="document_type")
    

    def __repr__(self):
        return f"<DocumentType(id={self.id}, name='{self.name}')>"


class Schema(Base):
    __tablename__ = "schemas"
    
    id = Column(Integer, primary_key=True, index=True)
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False)
    schema = Column(JSON, nullable=False)
    version = Column(String(10), default="1.0")
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now())
    
    # Relaciones
    document_type = relationship("DocumentType", back_populates="schemas")
    extractions = relationship("Extraction", back_populates="schema")

    def __repr__(self):
        return f"<DocumentSchema(id={self.id}, document_type_id={self.document_type_id}, schema='{self.schema}')>"


class Extraction(Base):
    __tablename__ = "extractions"
    
    id = Column(Integer, primary_key=True, index=True)
    schema_id = Column(Integer, ForeignKey("schemas.id"), nullable=False)
    document_text = Column(Text, nullable=False)
    result = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now())
    
    # Relación
    schema = relationship("Schema", back_populates="extractions")
    