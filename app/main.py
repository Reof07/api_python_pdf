from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

from .db.models.init_db import init_db
from .core.config import settings
from .api.routers.base_router import base_router
#from .extraction import data_extraction


app = FastAPI()


# Configuración de CORS: restringir a los orígenes permitidos en producción
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar la base de datos
init_db()
app.include_router(base_router)


@app.get("/info")
def read_root():
    return {
        "message": f" Hello, World! the app: {settings.APP_NAME} is Running in {settings.FASTAPI_ENV} mode."}
    
