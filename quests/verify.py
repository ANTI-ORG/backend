from abc import ABC, abstractmethod

from fastapi import Depends
from sqlalchemy.orm import Session

from app.crud import get_quest_by_id
from app.database import get_db
from app.models import Quest


class BaseQuest(ABC):
    """Абстрактный базовый класс для всех квестов."""

    def __init__(self, quest_id: int, db: Session = Depends(get_db)):
        self.db = db
        self.quest_object: Quest = self.get_quest_by_id(quest_id)

    def get_quest_by_id(self, quest_id: int) -> Quest:
        """Метод для получения квеста по ID из базы данных."""
        quest = get_quest_by_id(self.db, quest_id)
        if quest is None:
            raise ValueError(f"Quest with id {quest_id} not found.")
        return quest

    @abstractmethod
    def verify_task1(self) -> bool:
        """Проверка первой задачи квеста."""
        pass

    def set_completed(self) -> bool:
        """Установка поля completed модели Quest. Все verify_task1 должны вернуть true."""
        pass


class Quest1(BaseQuest):
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(quest_id=1)

    def verify_task1(self) -> bool:
        pass

    def verify_task2(self) -> bool:
        pass

    def verify_task3(self) -> bool:
        pass
