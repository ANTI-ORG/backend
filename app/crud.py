from datetime import timedelta, datetime

import pytz
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session, Query as QueryOrm
from random_username.generate import generate_username

from app import models
from app.models import IpAddress, WalletNetwork
from app.schemas import UsernameSchema


def get_object_or_404(model, db: Session, **kwargs):
    obj = db.query(model).filter_by(**kwargs).first()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found")
    return obj


def get_user_by_web3_address(db: Session, web3_address: str) -> models.User:
    wallet = db.query(models.Wallet).filter(models.Wallet.web3_address == web3_address).first()

    if wallet:
        return db.query(models.User).filter(models.User.id == wallet.user_id).first()

    return None


def get_user_by_id(db: Session, user_id: str) -> models.User:
    return get_object_or_404(models.User, db, id=user_id)


def get_quest_by_id(db: Session, quest_id: int) -> models.Quest:
    return get_object_or_404(models.Quest, db, id=quest_id)


def get_chain_by_id(db: Session, chain_id: int) -> models.Chain:
    return get_object_or_404(models.Chain, db, id=chain_id)


def get_project_by_id(db: Session, project_id: int) -> models.Project:
    return get_object_or_404(models.Project, db, id=project_id)

def get_task_by_id(db: Session, task_id: int) -> models.Project:
    return get_object_or_404(models.Task, db, id=task_id)


def update_docs_streak(db: Session, user: models.User):
    today = datetime.now(pytz.UTC).date()
    docs_grabbed_at = user.docs_grabbed_at

    if docs_grabbed_at and user.curr_docs_streak != 0:
        docs_grabbed_at = docs_grabbed_at.date()
        days_difference = (today - docs_grabbed_at).days
        if days_difference > 1:
            user.max_docs_streak = max(user.curr_docs_streak, user.max_docs_streak)
            if user.curr_docs_streak > 0:
                user.previous_docs_streak = user.curr_docs_streak
            user.curr_docs_streak = 0
            db.commit()

def get_quests_query(db: Session, filter: str = None) -> QueryOrm:
    if filter:
        filter = filter.lower()

    if filter == 'new':
        return db.query(models.Quest).order_by(models.Quest.created_at.desc())
    return db.query(models.Quest)


def get_chains(db: Session, filter: str = None):
    return db.query(models.Chain).all()


def get_projects(db: Session, filter: str = None):
    return db.query(models.Project).all()


def calculate_24h_online(db: Session):
    today_date = datetime.now(pytz.UTC).date()
    return db.query(models.IpAddress).filter(func.date(models.IpAddress.visited_at) == today_date).count()


def add_token_to_user(db: Session, user_id: str, access_token: str):
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")

        # Создаем новый объект Token
    new_token = models.Token(access_token=access_token, user_id=user_id)

    # Добавляем токен в сессию и связываем его с пользователем
    db.add(new_token)

    # Сохраняем изменения в базе данных
    db.commit()

    # Обновляем объект user, чтобы отразить изменения
    db.refresh(user)

    return new_token.access_token


def is_username_exist(db, username) -> bool:
    return db.query(models.User).filter(models.User.username == username).count() > 0


def generate_random_username(db, web3_address: str) -> str:
    for i in range(30):

        u = generate_username()[0]
        try:
            UsernameSchema(username=u)
        except ValueError as e:
            print(f'Username validation error: {e}')

        if not is_username_exist(db, u):
            return u
    else:
        return web3_address


def create_user(db: Session, web3_address: str, username: str = None) -> models.User:
    if not username:
        username = generate_random_username(db, web3_address)

    db_user = models.User(
        username=username
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def add_or_update_ip_address(db: Session, client_ip: str):
    existing_ip = db.query(IpAddress).filter(IpAddress.ip == client_ip).first()

    if existing_ip:
        # Если запись найдена, обновить visited_at
        existing_ip.visited_at = func.now()
    else:
        new_ip = IpAddress(ip=client_ip)
        db.add(new_ip)

    db.commit()


def add_ip_to_user(db: Session, user_id: int, client_ip: str):
    # Получаем объект адреса
    ip_address_object = db.query(models.IpAddress).filter(models.IpAddress.ip == client_ip).first()

    if not ip_address_object:
        ip_address_object = models.IpAddress(ip=client_ip)
        db.add(ip_address_object)
        db.commit()
        db.refresh(ip_address_object)

    # Получаем пользователя
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=400, detail='User not found')

    # Проверяем, существует ли уже ассоциация
    association = db.query(models.user_ip).filter(
        models.user_ip.c.user_id == user_id,
        models.user_ip.c.ip_address_id == ip_address_object.id
    ).first()

    if association:
        # Обновляем время последнего доступа
        db.execute(
            models.user_ip.update().where(
                models.user_ip.c.user_id == user_id,
                models.user_ip.c.ip_address_id == ip_address_object.id
            ).values(visited_at=func.now())
        )
        db.commit()
        print("IP address updated with new access time.")
    else:
        # Создаем новую запись в связной таблице
        db.execute(
            models.user_ip.insert().values(
                user_id=user_id,
                ip_address_id=ip_address_object.id,
                visited_at=func.now()
            )
        )
        db.commit()
        print("IP address added to user.")

    # Получаем обновленное время из смежной таблицы
    updated_time = db.execute(
        select(models.user_ip.c.visited_at).where(
            models.user_ip.c.user_id == user_id,
            models.user_ip.c.ip_address_id == ip_address_object.id
        )
    ).scalar_one_or_none()

    if updated_time:
        ip_address_object.visited_at = updated_time

    db.commit()


def get_user_ips(db: Session, web3_address: str) -> list[str]:
    try:
        # Найти пользователя по web3_address
        user = get_user_by_web3_address(db, web3_address)

        # Получить все IP-адреса, связанные с пользователем
        ip_addresses = db.query(models.IpAddress).join(
            models.user_ip
        ).filter(
            models.user_ip.c.user_id == user.id
        ).all()

        # Возвращаем IP-адреса в виде списка строк
        return [ip.ip for ip in ip_addresses]

    except NoResultFound:
        # Если пользователь не найден, возвращаем пустой список или обрабатываем ошибку по-другому
        return []


def verify_token_in_db(db: Session, token: str):
    # Выполнение асинхронного запроса к базе данных
    result = db.execute(select(models.Token).filter(models.Token.access_token == token))
    token_record = result.scalars().first()

    if token_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_record.access_token


def deactivate_token(db: Session, token: str):
    db.query(models.Token).filter(models.Token.access_token == token).delete()
    db.commit()


def link_web3_address(db: Session, user: models.User, web3_address: str,
                      wallet_network: WalletNetwork) -> models.Wallet:
    # Проверяем, существует ли уже кошелек с этим web3_address
    existing_wallet = db.query(models.Wallet).filter_by(web3_address=web3_address).first()

    if existing_wallet:
        raise HTTPException(status_code=400, detail="This wallet address is already linked to the user")

    # Создаем новый кошелек
    new_wallet = models.Wallet(
        web3_address=web3_address,
        wallet_network=wallet_network,
        user_id=user.id
    )

    try:
        db.add(new_wallet)
        db.commit()
        db.refresh(new_wallet)
        return new_wallet
    except Exception as e:
        print("Error while linking wallet to user", user.id)
        db.rollback()
        raise HTTPException(status_code=400, detail="Error while linking wallet to user")
