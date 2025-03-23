from fastapi import APIRouter


from ..routers.extraction_routers import extraction_router


base_router = APIRouter()

routers = [
    extraction_router
]

for router in routers:
    base_router.include_router(router)
