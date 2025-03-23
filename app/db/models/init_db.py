
from ..database import engine, Base
from ...core.logger_config import logger 
from ..models.user import User
from ..models.extraction_model import (
    DocumentType,
    Schema,
    Extraction
)


def init_db():
    """Create the database tables."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise 
    