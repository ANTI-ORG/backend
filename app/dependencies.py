from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.crud import verify_token_in_db
from app.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="")


def verify_token(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    token = verify_token_in_db(db, token)
    return token
