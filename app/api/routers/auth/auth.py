from fastapi import( 
    APIRouter,
    status,
    Depends,
    HTTPException
    )
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ....db.database import get_db
from ....schemas.user_schema import  UserRegister
from ....schemas.generic import GenericResponse
from ....service.user_service import (
    register_user,
    get_refresh_token
    )
from ....service.authentication import (
    authenticate_user,
    create_access_token,
    create_refresh_token
    )

auth_router = APIRouter(
    prefix="/authentication",
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)

class LoginRequest(BaseModel):
    email: str
    password: str

@auth_router.post(
    "/signin",
    operation_id="signin",
    summary="User Login",
    description="Endpoint to authenticate a user by verifying their email and password. Returns an access token and a refresh token upon successful authentication.",
    status_code=status.HTTP_200_OK,
    response_description="Access and refresh tokens for the authenticated user."
)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
)-> GenericResponse:
    user = authenticate_user(request.email, request.password, db)
    print(user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(db=db, email=user.email)
    return GenericResponse(
            message="Successfully created the user",
            data={
                # "user": user,
                "access_token": access_token, 
                "refresh_token": refresh_token, 
                "token_type": "bearer"
            }
        )



@auth_router.post(
    "/signup",
    operation_id="signup",
    summary="User Registration",
    description="Endpoint to register a new user by providing the required information such as email and password. Returns the user details upon successful registration.",
    status_code=status.HTTP_201_CREATED,
    response_description="Details of the newly registered user."
)
async def register(
    user: UserRegister,
    db: Session = Depends(get_db)
) -> GenericResponse:
    try:
        user_registered = await register_user(user, db)
        return GenericResponse(
            message="Successfully created the user",
            data={"user_registered": user_registered}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
        

@auth_router.post("/refresh")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    user = get_refresh_token(db, refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.refresh_token_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Crear un nuevo access token
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
