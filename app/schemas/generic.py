from pydantic import BaseModel
from typing import List

class GenericResponse(BaseModel):
    message: str
    detail: str = None  
    data: dict = None 
    
    
# Respuestas comunes
# common_responses = {
#     200: {
#         "description": "Operación exitosa",
#         "content": {
#             "application/json": {
#                 "example": {
#                     "message": "Operación completada exitosamente",
#                     "data": {}
#                 }
#             }
#         }
#     },
#     401: {
#         "description": "Unauthorized, token inválido o faltante",
#         "content": {
#             "application/json": {
#                 "example": {"detail": "Token no válido o faltante"}
#             }
#         }
#     },
#     500: {
#         "description": "Error interno del servidor",
#         "content": {
#             "application/json": {
#                 "example": {"detail": "Error inesperado: algo salió mal"}
#             }
#         }
#     }
# }