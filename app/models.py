import enum
import re
import uuid
from datetime import datetime, timezone
from typing import ClassVar

from pydantic import ValidationError
from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from app.database import Base

# Промежуточная таблица many-to-many для User и Quest с состоянием квеста
user_quest = Table(
    'user_quest', Base.metadata,
    Column('user_id', String(36), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('quest_id', Integer, ForeignKey('quests.id', ondelete="CASCADE"), primary_key=True),
    Column('completed', Boolean, default=False)
)

# Промежуточная таблица many-to-many для User и IpAddress
user_ip = Table(
    'user_ip', Base.metadata,
    Column('user_id', String(36), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('ip_address_id', Integer, ForeignKey('ip_addresses.id', ondelete="CASCADE"), primary_key=True),
    Column('visited_at', DateTime(timezone=True), default=datetime.now(timezone.utc))
)

user_task_association = Table(
    'user_tasks',
    Base.metadata,
    Column('user_id', String(36), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('completed', Boolean, default=False, nullable=False)
)


class WalletNetwork(enum.Enum):
    Ethereum = "ethereum"
    Solana = "solana"


# Модель Wallet
class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    web3_address = Column(String(100), unique=True, index=True, nullable=False)
    wallet_network = Column(Enum(WalletNetwork), nullable=False)  # Enum для выбора типа кошелька
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False)  # Внешний ключ на пользователя

    user = relationship("User", back_populates="wallets")

    def __str__(self):
        return f"id: {self.id}, web3_address: {self.web3_address}"


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String, nullable=False)
    button_text = Column(String(40), nullable=False, default='Open')
    button_link = Column(String(), nullable=False)
    filepath = Column(String, nullable=False, default='image/task/default.jpeg')

    file = None  # dummy field (admin panel)

    quest_id = Column(Integer, ForeignKey('quests.id', ondelete="CASCADE"), nullable=False)
    quest = relationship("Quest", back_populates="tasks")
    # Устанавливаем связь "многие ко многим" через смежную таблицу
    users = relationship('User', secondary=user_task_association, back_populates='tasks', cascade="all, delete")

    def __str__(self):
        return f"id: {self.id}, title: {self.title}"


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    username = Column(String(50), index=True, unique=True, nullable=False)
    xp = Column(Integer, default=0)
    rang_id = Column(Integer, default=1)
    max_docs_streak = Column(Integer, default=0)
    curr_docs_streak = Column(Integer, default=0)
    previous_docs_streak = Column(Integer, default=0)
    docs_grabbed_at = Column(DateTime(timezone=True), default=None, nullable=True)
    registered_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    filepath = Column(String, nullable=False, default='image/avatar/default.jpeg')

    file = None  # dummy field

    # Связь с Quest через промежуточную таблицу
    quests = relationship("Quest", secondary=user_quest, back_populates="users", cascade="all, delete")
    # Связь с IpAddress через промежуточную таблицу
    ip_addresses = relationship("IpAddress", secondary=user_ip, back_populates="users", cascade="all, delete")
    # Связь с Token (один пользователь может иметь много токенов)
    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    # Связь с Wallet (один пользователь может иметь много кошельков)
    wallets = relationship("Wallet", back_populates="user", cascade="all, delete-orphan")
    # Устанавливаем связь "многие ко многим" через смежную таблицу
    tasks = relationship('Task', secondary=user_task_association, back_populates='users', cascade="all, delete")

    @validates('username')
    def validate_username(self, key, value):
        if len(value) < 5:
            raise ValueError("Username must be at least 5 characters long")
        if len(value) > 50:
            raise ValueError("Username must be less than 50 characters long")
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return value

    @validates('rang_id')
    def validate_rang_id(self, key, value):
        if len(value) < 1:
            raise ValueError("Rang id must be gte 1")
        if len(value) > 5:
            raise ValueError("Rang id must be lte 5")
        return value

    def __str__(self):
        return f"id: {self.id}, username: {self.username}"


class Quest(Base):
    __tablename__ = "quests"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(70), nullable=False)
    description = Column(String, nullable=False)
    xp = Column(Integer, default=0)
    filepath = Column(String, nullable=False, default='image/quest/default.jpeg')
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    task_count: ClassVar[int]
    file = None  # dummy field (admin panel)

    chain_id = Column(Integer, ForeignKey('chains.id', ondelete="SET NULL"))
    chain = relationship("Chain", back_populates="quests")

    project_id = Column(Integer, ForeignKey('projects.id', ondelete="SET NULL"))
    project = relationship("Project", back_populates="quests")

    # Связь с User через промежуточную таблицу
    users = relationship("User", secondary=user_quest, back_populates="quests", cascade="all, delete")
    # Связь с Task (один квест может иметь много задач)
    tasks = relationship("Task", back_populates="quest", cascade="all, delete-orphan")

    def __str__(self):
        return f"id: {self.id}, title: {self.title}"


class Admin(Base):
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)  # Primary key для токенов
    access_token = Column(String(1024), nullable=False, unique=True, index=True)

    # Foreign key, связывающий токен с пользователем
    user_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

    # Обратная связь с пользователем
    user = relationship("User", back_populates="tokens")


class IpAddress(Base):
    __tablename__ = "ip_addresses"
    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String(39), index=True, unique=True)
    visited_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), index=True)

    # Связь с User через промежуточную таблицу
    users = relationship("User", secondary=user_ip, back_populates="ip_addresses", cascade="all, delete")

    def __str__(self):
        return f"id: {self.id}, ip: {self.ip}"


class Chain(Base):
    __tablename__ = "chains"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    filepath = Column(String, nullable=False, default='image/chain/default.jpeg')

    file = None  # dummy field (admin panel)

    quests = relationship("Quest", back_populates="chain")

    def __str__(self):
        return f"id: {self.id}, name: {self.name}"


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    filepath = Column(String, nullable=False, default='image/project/default.jpeg')

    file = None  # dummy field (admin panel)

    quests = relationship("Quest", back_populates="project")

    def __str__(self):
        return f"id: {self.id}, name: {self.name}"
