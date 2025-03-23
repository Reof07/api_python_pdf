from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    model_validator
    )
from typing import Optional

from sqlalchemy.orm import Session
from ..db.database import get_db



class UserBase(BaseModel):
    username: str = Field(
        ..., examples=["example"], description="User's username"
    )
    email: EmailStr = Field(
        ..., examples=["example@example.com"], description="User's email"
    )
    
class User (UserBase):
    name: Optional[str] = Field(
        None, examples=["John Doe"], description="User's name"
    )
    last_name: Optional[str] = Field(
        None, examples=["Doe"], description="User's last name"
    )
    
class UserRegister(UserBase):
    password: str = Field(
        ..., examples=["example"], description="User's password"
    )
