from fastapi import (
    APIRouter
    )


summarize_router = APIRouter(
    prefix="/summarize",
    tags=["summarize"],
    responses={404: {"description": "Not found"}},
)

@summarize_router.post("/")
async def summarize():
    return {"message": "Hello, world!"}