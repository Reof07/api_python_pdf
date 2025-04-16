from fastapi import APIRouter


from ..routers.extraction_routers import extraction_router
from ..routers.summarize import summarize_router


base_router = APIRouter()

routers = [
    extraction_router,
    summarize_router
]

for router in routers:
    base_router.include_router(router)
