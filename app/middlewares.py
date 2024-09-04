import json

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, JSONResponse
from starlette.requests import Request

from admin.routers import get_current_admin
from app.crud import add_or_update_ip_address, add_ip_to_user
from app.database import get_db
from app.utils import get_user_from_token
from authentication.auth import extract_token_from_header_value
import os
from dotenv import load_dotenv

load_dotenv()
ADMIN_SEED_PARAMETER = os.getenv('ADMIN_SEED_PARAMETER')


class AuthAdminMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        # Игнорируем все пути кроме /admin/
        if 'admin' not in request.url.path:
            response = await call_next(request)
            return response

        access_token = request.cookies.get('access_token')
        if access_token:
            # Валидириуем токен
            admin = get_current_admin(access_token)

            if admin:
                response = await call_next(request)
                return response

        seed_value = None
        method = request.method
        if method == "GET":
            query_params = request.query_params
            seed_value = query_params.get('seed')

        if method == "POST":
            try:
                # Пытаемся распарсить тело запроса
                body_data = json.loads(await request.body())
                seed_value = body_data.get('seed')
            except:
                pass

        if seed_value != ADMIN_SEED_PARAMETER:
            return JSONResponse(
                status_code=404,
                content={"detail": "Not Found"}
            )

        if request.url.path == f'/admin/':
            return RedirectResponse(url=f'/auth/admin?seed={seed_value}')


        response = await call_next(request)
        return response


class IpCollectorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip_address = self.get_client_ip(request)

        authorization_header = request.headers.get('Authorization')
        try:
            access_token = extract_token_from_header_value(authorization_header)
        except HTTPException as e:
            access_token = None

        db = next(get_db())

        try:
            user = get_user_from_token(db, access_token)
        except Exception as e:
            user = None

        if user:
            # Если пользователь авторизован, связываем IP с пользователем
            add_ip_to_user(db, user.id, ip_address)
        else:
            # Если токен отсутствует или невалидный, записываем IP-адрес в таблицу IpAddress
            add_or_update_ip_address(db, ip_address)

        # Продолжаем обработку запроса
        response = await call_next(request)
        return response

    @staticmethod
    def get_client_ip(request: Request) -> str:
        x_forwarded_for = request.headers.get('x-forwarded-for')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.client.host
        return ip_address
