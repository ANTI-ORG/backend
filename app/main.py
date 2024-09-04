from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqladmin import Admin
import uvicorn
from dotenv import load_dotenv
import os

from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_pagination import add_pagination

from admin.crud import create_admin_user
from admin.routers import admin_router
from app.limiter import limiter
from app.middlewares import AuthAdminMiddleware, IpCollectorMiddleware
from app.routers import router
from admin.admin_panel import UserAdmin, QuestAdmin, ProjectAdmin, ChainAdmin, WalletAdmin, TaskAdmin
from app.database import engine, get_db
from s3_manager.routers import file_router
from authentication.routers import auth_router


load_dotenv()
ADMIN_LOGIN = os.getenv('ADMIN_LOGIN')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')


app = FastAPI()

add_pagination(app)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(AuthAdminMiddleware)  # Кастомная авторизация по токену
app.add_middleware(IpCollectorMiddleware)  # Сбор входящих ip адресов
app.mount("/static", StaticFiles(directory="static"), name="static")


# Настройка CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает запросы с любого домена
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Настраиваем Admin и добавляем наши ModelView
admin = Admin(app, engine)
admin.add_view(UserAdmin)
admin.add_view(QuestAdmin)
admin.add_view(TaskAdmin)
admin.add_view(ProjectAdmin)
admin.add_view(ChainAdmin)
admin.add_view(WalletAdmin)
app.include_router(router)
app.include_router(auth_router, prefix="/auth")
app.include_router(file_router, prefix="/files")
app.include_router(admin_router, prefix="/auth/admin")



@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    create_admin_user(db, ADMIN_LOGIN, ADMIN_PASSWORD)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
