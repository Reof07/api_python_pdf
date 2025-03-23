
from sqlalchemy.orm import Session

from ..schemas.user_schema import UserRegister, UserBase
from app.core.logger_config import logger
from app.db.models.user import User
from ..utils.hash_password import pwd_context


def save_new_user(db: Session, user: UserRegister)-> User:
    """Save a new user to the database.

    Args:
        db (Session): The database session.
        user (UserRegister): The user object to be saved.

    Returns:
        User
    """
    try:
        user = User(
            username = user.username,
            email = user.email,
            hashed_password=pwd_context.hash(user.password)
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)

        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error al guardar el usuario en la base de datos: {str(e)}")
        raise ValueError(f"Error al guardar el usuario en la base de datos: {str(e)}")
        
        
def check_if_user_exists(db: Session, username: str)-> bool:
    """Check if a user with the given username exists in the database.

    Args:
        db (Session): The database session.
        username (str): The username to check.

    Returns:
        bool: True if the user exists, False otherwise.
    """
    return db.query(User).filter(User.username == username).first() is not None

async def register_user(user: UserRegister, db: Session)-> UserBase:
    """Register a new user in the database.

    Args:
        user (UserRegister): The user object to be registered.

    Returns:
        UserRegister
    """

    if check_if_user_exists(db, user.username):
        raise ValueError("El usuario ya existe")
    
    new_user = save_new_user(db, user)    
    return UserBase(username=new_user.username, email=new_user.email)

def get_user_by_email(db: Session, email: str):
    """ Get user by email

    Args:
        db (Session): The database session.
        email (str): The email of the user to be retrieved.

    Returns:
        User
    """
    return db.query(User).filter(User.email == email).first()

def get_refresh_token(db: Session, refresh_token: str):
    """ Get refresh token

    Args:
        db (Session): The database session.
        refresh_token (str): The refresh token of the user to be retrieved.

    Returns:
        User        
    """
    return db.query(User).filter(User.refresh_token == refresh_token).first()