from admin.routers import get_current_admin
from fastapi import HTTPException
from starlette.requests import Request


def check_admin_access(request: Request) -> bool:
    token = request.cookies.get("access_token")
    admin = get_current_admin(token=token)
    if admin:
        return True
    return False


def is_admin(request: Request) -> bool:
    if not check_admin_access(request):
        raise HTTPException(status_code=403, detail="Access Denied")
    return True