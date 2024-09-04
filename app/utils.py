import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

import jwt
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.crud import get_user_by_web3_address
from app.schemas import TimeLeft

load_dotenv()
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = "HS256"


def get_user_from_token(db: Session, token: str):
    payload = decode_token(token)
    web3_user_address = payload.get("sub")

    if web3_user_address is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_web3_address(db, web3_user_address)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User with specified web3_address not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_time_until_midnight():
    now = datetime.now()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_diff = midnight - now

    hours, remainder = divmod(time_diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return {'hours': hours, 'minutes': minutes, 'seconds': seconds}


def decode_token(token: str):
    if not token:
        raise HTTPException(status_code=401, detail="Token not provided", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )