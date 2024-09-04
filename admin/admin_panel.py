from typing import Any

from sqladmin.fields import FileField

from app.database import get_db
from app.models import User, Quest, Project, Chain, Wallet, Task
from fastapi import Request
from sqladmin import ModelView
from admin.dependencies import check_admin_access, is_admin
from s3_manager.routers import upload_any_on_s3


class AdminSchema(ModelView):
    file_dir = ''

    def is_accessible(self, request: Request) -> bool:
        return check_admin_access(request)

    async def scaffold_form(self):
        form_class = await super().scaffold_form()

        if hasattr(self.model, 'filepath'):
            form_class.file = FileField('Upload File')

        return form_class

    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        file = data.get('file', None)

        if model.id is None:
            await super().on_model_change(data, model, is_created, request)
            return

        if file and file.size > 0:
            await self.upload_s3(file, request, model)

        data.pop('file')
        await super().on_model_change(data, model, is_created, request)

    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        # Обработка после создания/изменения объекта
        file = data.get('file', None)

        if file and file.size > 0:
            await self.upload_s3(file, request, model)

        await super().after_model_change(data, model, is_created, request)

    async def upload_s3(self, file, request: Request, obj: Any):
        if file and file.size > 0:
            have_access = is_admin(request)
            filepath = await upload_any_on_s3(self.file_dir, obj.id, file, next(get_db()), have_access)
            setattr(obj, 'filepath', filepath)


class UserAdmin(AdminSchema, model=User):
    file_dir = 'avatar'

    column_list = [User.id, User.username, User.xp, User.max_docs_streak,
                   User.curr_docs_streak, User.previous_docs_streak, User.docs_grabbed_at, User.registered_at,
                   User.filepath]
    form_columns = [User.id, User.username, User.xp, User.max_docs_streak,
                    User.curr_docs_streak, User.previous_docs_streak, User.docs_grabbed_at, User.registered_at]


class QuestAdmin(AdminSchema, model=Quest):
    file_dir = 'quest'

    column_list = [Quest.id, Quest.title, Quest.description, Quest.xp, Quest.filepath,
                   Quest.chain_id, Quest.project_id, Quest.created_at]
    form_columns = [Quest.id, Quest.title, Quest.description, Quest.xp,
                    Quest.chain, Quest.project, Quest.created_at]


class ProjectAdmin(AdminSchema, model=Project):
    file_dir = 'project'

    column_list = [Project.id, Project.name, Project.filepath]
    form_columns = [Project.id, Project.name, Project.quests]


class ChainAdmin(AdminSchema, model=Chain):
    file_dir = 'chain'

    column_list = [Chain.id, Chain.name, Chain.filepath]
    form_columns = [Chain.id, Chain.name, Chain.quests]


class TaskAdmin(AdminSchema, model=Task):
    file_dir = 'task'

    column_list = [Task.id, Task.title, Task.description, Task.button_text, Task.button_link, Task.filepath,
                   Task.quest_id]
    form_columns = [Task.title, Task.description, Task.button_text, Task.button_link, Task.quest_id, Task.quest]


class WalletAdmin(AdminSchema, model=Wallet):
    column_list = [Wallet.id, Wallet.web3_address, Wallet.wallet_network, Wallet.user_id]
    form_columns = [Wallet.id, Wallet.web3_address, Wallet.wallet_network, Wallet.user_id]
