from fastapi import Depends, HTTPException, status, APIRouter, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timezone

from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()
import os

from admin.crud import get_admin
from admin.schemes import AdminToken, AdminLogin
from app.database import SessionLocal, get_db
from admin.security import verify_password, create_access_token
from app.models import Admin

from app.utils import JWT_SECRET_KEY, ALGORITHM

ADMIN_SEED_PARAMETER = os.getenv('ADMIN_SEED_PARAMETER')


admin_router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme_admin = OAuth2PasswordBearer(tokenUrl="auth/admin")

templates = Jinja2Templates(directory="static/html")

@admin_router.get("/", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "seed": ADMIN_SEED_PARAMETER})


@admin_router.post("/token", response_model=AdminToken)
async def login(form_data: AdminLogin, db: Session = Depends(get_db)):
    admin = get_admin(db, form_data.username)
    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": admin.username}, minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response


def get_current_admin(token: str = Depends(oauth2_scheme_admin)) -> Admin:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Декодируем токен
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        # Проверяем срок действия токена
        if 'exp' in payload:
            exp_timestamp = payload['exp']
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            if exp_datetime < datetime.now(tz=timezone.utc):
                raise credentials_exception
        else:
            raise credentials_exception

    except Exception as e:
        return None

    # Получаем администратора из базы данных
    admin = get_admin(SessionLocal(), username=username)

    return admin
