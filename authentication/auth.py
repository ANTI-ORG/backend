import random
import string
from sqlalchemy.orm import Session
from app import crud
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta

import jwt
from dotenv import load_dotenv

from app.crud import add_ip_to_user, add_token_to_user, link_web3_address, get_user_by_web3_address
from app.models import WalletNetwork
from app.utils import get_user_from_token, decode_token, JWT_SECRET_KEY, ALGORITHM
from authentication.wallet_validators import validate_ethereum_wallet, validate_solana_wallet

load_dotenv()

# Загрузка переменных окружения
ACCESS_TOKEN_EXPIRE_MINUTES = 10080
TEMP_TOKEN_EXPIRE_SECONDS = 120


# Функция для создания временного токена
def create_temp_token(address: str, nonce: str):
    expire = datetime.now(timezone.utc) + timedelta(seconds=TEMP_TOKEN_EXPIRE_SECONDS)
    to_encode = {"sub": address, "nonce": nonce, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Функция для создания долгосрочного JWT токена
def create_access_token(address: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": address, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Функция для декодирования и проверки токена


def generate_nonce(db: Session, web3_address: str) -> str:
    nonce = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    # Создаем временный токен
    temp_token = create_temp_token(web3_address, nonce)

    return temp_token


def verify_signature(db: Session, temp_token: str, signature: str, client_ip: str,
                     access_token: str = None) -> dict | None:
    payload = decode_token(temp_token)
    web3_address = payload.get("sub")
    nonce = payload.get("nonce")

    if not web3_address:
        raise HTTPException(status_code=400, detail="Invalid token payload")

    if not nonce:
        raise HTTPException(status_code=400, detail="Nonce not set")

    network = get_wallet_network(web3_address)

    wallet_is_valid = False
    try:
        if network == WalletNetwork.Ethereum:
            wallet_is_valid = validate_ethereum_wallet(web3_address, nonce, signature)
        elif network == WalletNetwork.Solana:
            wallet_is_valid = validate_solana_wallet(web3_address, nonce, signature)
        else:
            available_networks = ', '.join(wallet_type.value for wallet_type in WalletNetwork)
            raise HTTPException(status_code=400,
                                detail=f"Wallet network not allowed! Available networks: {available_networks}")

    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if not wallet_is_valid:
        raise HTTPException(status_code=400, detail="Invalid signature")

    user = None
    if access_token:
        try:
            user = get_user_from_token(db, access_token)
            link_web3_address(db, user, web3_address, network)
        except Exception as e:
            print(e)
            raise HTTPException(status_code=400, detail="Wallet connected to user not found")
    else:
        user = get_user_by_web3_address(db, web3_address)

    if not user:
        user = crud.create_user(db, web3_address)
        link_web3_address(db, user, web3_address, network)

    add_ip_to_user(db, user.id, client_ip)  # Регистрируем ip с которого прошла регистрация

    if not access_token:
        access_token = create_access_token(web3_address)  # Создаем долгосрочный токен
        add_token_to_user(db, user.id, access_token)  # Привязываем токен к пользователю

    return {"access_token": access_token, 'web3_address': web3_address,
            'wallet_network': network}


def validate_token(db: Session, token: str) -> bool:
    try:
        payload = decode_token(token)
    except:
        return False

    web3_address = payload.get("sub")

    if not web3_address:
        return False

    user = crud.get_user_by_web3_address(db, web3_address)
    if not user:
        return False

    return True


def extract_token_from_header_value(auth_header_value: str):
    if not auth_header_value or not auth_header_value.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Authorization header",
        )

    return auth_header_value.split(" ")[1]


def get_wallet_network(web3_address: str):
    if web3_address.startswith("0x") and len(web3_address) == 42:
        return WalletNetwork.Ethereum
    elif len(web3_address) == 44 and web3_address.isalnum():
        return WalletNetwork.Solana
