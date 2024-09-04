from fastapi import APIRouter, Depends, HTTPException, Request, status, Response
from sqlalchemy.orm import Session

from app.crud import deactivate_token, link_web3_address
from app.database import get_db
from app.dependencies import verify_token
from app.limiter import limiter
from app.utils import get_user_from_token
from authentication import schemas

from authentication.auth import generate_nonce, verify_signature, validate_token, extract_token_from_header_value
from authentication.crud import delete_expired_tokens
from authentication.schemas import VerifySignatureRequest

auth_router = APIRouter()


@auth_router.post("/web3/generate-nonce", response_model=schemas.UserTempAuth)
@limiter.limit("8/minute")
def generate_nonce_route(request: Request, address: str, db: Session = Depends(get_db)):
    try:
        # Используем IP-адрес в функции и генерируем временный токен
        temp_token = generate_nonce(db, address)
        return {"temp_token": temp_token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.post("/web3/verify-signature", response_model=schemas.UserAuth)
@limiter.limit("8/minute")
def verify_signature_route(request: Request, body: VerifySignatureRequest, type: str, db: Session = Depends(get_db)):

    try:
        delete_expired_tokens(db)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail='Error while handling token')

    if type == 'sign_in':
        try:
            client_ip = request.client.host
            result = verify_signature(db, body.temp_token, body.signature, client_ip)
            web3_address = result['web3_address']
            token = result["access_token"]

            return {"access_token": token, "message": f'Wallet {web3_address} has been registered successfully'}
        except Exception as e:
            print(e)
            raise HTTPException(status_code=400, detail='Error while verifying signature')

    elif type == 'link':
        try:
            client_ip = request.client.host
            token = verify_token()
            result = verify_signature(db, body.temp_token, body.signature, client_ip, token)
            web3_address = result['web3_address']

            return {"access_token": token, "message": f'Wallet {web3_address} has been linked successfully'}
        except Exception as e:
            print(e)
            raise HTTPException(status_code=400, detail='Error while verifying signature')

    else:
        raise HTTPException(status_code=400, detail='Unsupported type! Available types: link, sign_in')


@auth_router.get("/web3/is-valid", response_model=schemas.TokenValid)
def is_valid_token(request: Request, db: Session = Depends(get_db)):
    try:
        token = extract_token_from_header_value(request.headers.get('Authorization'))

        is_valid = validate_token(db, token)

        return {"is_valid": is_valid}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.delete("/web3/deactivate")
def deactivate_user(db: Session = Depends(get_db), token: str = Depends(verify_token)):
    try:
        deactivate_token(db, token)

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
