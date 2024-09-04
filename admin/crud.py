from sqlalchemy.orm import Session

from admin.security import pwd_context
from app.models import Admin


def get_admin(db: Session, username: str):
    return db.query(Admin).filter(Admin.username == username).first()

def create_admin_user(db: Session, username, password):
    # Проверяем, существует ли уже пользователь с таким именем
    existing_admin = db.query(Admin).filter_by(username=username).first()

    if existing_admin:
        print(f"Admin user '{username}' already exists.")
    else:
        # Хэшируем пароль и создаем нового администратора
        hashed_password = pwd_context.hash(password)
        new_admin = Admin(username=username, hashed_password=hashed_password)
        db.add(new_admin)
        db.commit()
        print(f"Admin user '{username}' created successfully.")