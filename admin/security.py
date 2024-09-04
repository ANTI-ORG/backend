from datetime import datetime, timezone, timedelta

import jwt
from passlib.context import CryptContext

from app.utils import JWT_SECRET_KEY, ALGORITHM

# Создаем контекст для хеширования паролей
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, minutes: int = 15):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)

    to_encode.update({"sub": "admin", "exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
