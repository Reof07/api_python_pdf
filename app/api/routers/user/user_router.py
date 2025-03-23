from fastapi import (
    APIRouter,
    status,
    Depends,
    HTTPException
    )

from sqlalchemy.orm import Session

from ....db.database import get_db
from ....schemas.user_schema import UserRegister
from ....schemas.generic import GenericResponse
from ....service.user_service import register_user

user_router = APIRouter(
    prefix="/users",
    tags=["User"],    
    responses={404: {"description": "Not found"}},
)

@user_router.get(
    "/",
    summary="Get users",
    description="Get all users",
)
async def get_users():
    return {"message": "Hello, World! Get users"}

@user_router.post(
    "/",
    summary = "Create new user",
    description = "Create a new user in the system.",
    # status_code = status.HTTP_201_CREATED,
)
async def create_user(
    user: UserRegister,
    db: Session = Depends(get_db)
)-> GenericResponse:
    try:
        user_registered = await register_user(user, db)
        return GenericResponse(
            message="Successfully created the user",
            data = {
                "user_registered": "user_registered"
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@user_router.get(
    "/{user_id}",
    summary="Get user by id",
    description="Get user by id",
)
async def get_user_by_id(user_id: int):
    return {"message": "Hello, World! Get user by id"}

@user_router.put(
    "/{user_id}",
    summary="Update user by id",
    description="Update user by id",
)
async def update_user_by_id(user_id: int):
    return {"message": "Hello, World! Update user by id"}

@user_router.delete(
    "/{user_id}",
    summary="Delete user by id",
    description="Delete user by id",
)
async def delete_user_by_id(user_id: int):
    return {"message": "Hello, World! Delete user by id"}