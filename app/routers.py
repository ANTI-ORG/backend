import json
from datetime import timezone
from functools import partial
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import ValidationError
from dotenv import load_dotenv

from app.database import get_db
from app.dependencies import verify_token
from app.schemas import UserBase, QuestBase, ProjectBase, ChainBase, CanGrabDocs, GrabDocs, CountUsers, \
    UserPatchRequest, UserPatchResponse, TaskBase, QuestShortData
from app.crud import *
from app.utils import get_user_from_token, get_time_until_midnight
from s3_manager.routers import gen_presigned_url, upload_avatar_on_s3

load_dotenv()

router = APIRouter()


@router.get("/user/", response_model=UserBase)
async def return_user_route(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = get_user_from_token(db, token)
    update_docs_streak(db, user)
    user.avatar = await gen_presigned_url(user.filepath)
    return user


@router.patch("/user/", response_model=UserPatchResponse)
async def edit_user(patch_data: UserPatchRequest, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = get_user_from_token(db, token)

    # Обновляем username, если он передан
    if patch_data.username:
        try:
            user.username = patch_data.username
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Обновляем аватар, если передана картинка в base64
    if patch_data.base64_image:
        try:
            await upload_avatar_on_s3(patch_data.base64_image, token, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error saving avatar")

    # Сохраняем изменения в БД
    db.commit()

    return {"status": "success", "user": await return_user_route(token, db)}


@router.get("/quest/{quest_id}", response_model=QuestBase)
async def return_quest(quest_id: int, db: Session = Depends(get_db), short_desc: bool = False):
    if not quest_id:
        raise HTTPException(status_code=400, detail="Quest id must be provided")

    quest = get_quest_by_id(db, quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    quest.quest_image = await gen_presigned_url(quest.filepath)

    if quest.chain_id is not None:
        chain = await return_chain(quest.chain_id, db)
        quest.chain_name = chain.name
        quest.chain_image = chain.image

    if quest.project_id is not None:
        project = await return_project(quest.project_id, db)
        quest.project_name = project.name
        quest.project_image = project.image

    quest.task_count = len(quest.tasks)

    if not short_desc:
        quest.tasks = [await return_task(task.id, db) for task in quest.tasks]

    return quest


async def quests_transformer(db: Session, items: list[models.Quest]) -> List[QuestShortData]:
    return [await return_quest(item.id, db, True) for item in items]


@router.get("/quests", response_model=Page[QuestShortData])
async def return_quests(
        db: Session = Depends(get_db),
        filter: Optional[str] = Query(None, alias="filter",
                                      description="Filter quests based on the given criteria. Use 'new' to get the latest quests.",
                                      example="new")
):
    quests_query = get_quests_query(db, filter=filter)
    pagination_object = paginate(db, quests_query)
    pagination_object.items = await quests_transformer(db, pagination_object.items)

    return pagination_object


@router.get("/projects", response_model=List[ProjectBase])
def return_projects(db: Session = Depends(get_db)):
    projects = get_projects(db)
    return [return_project(x.id, db) for x in projects]


@router.get("/chains", response_model=List[ChainBase])
def return_chains(db: Session = Depends(get_db)):
    chains = get_chains(db)
    return [return_chain(x.id, db) for x in chains]


@router.get("/task/{task_id}", response_model=TaskBase)
async def return_task(task_id: int, db: Session = Depends(get_db)):
    if not task_id:
        raise HTTPException(status_code=400, detail="Task id must be provided")

    task = get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.image = await gen_presigned_url(task.filepath)

    return task


@router.get("/project/{project_id}", response_model=ProjectBase)
async def return_project(project_id: int, db: Session = Depends(get_db)):
    if not project_id:
        raise HTTPException(status_code=400, detail="Project id must be provided")

    project = get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.image = await gen_presigned_url(project.filepath)

    return project


@router.get("/chain/{chain_id}", response_model=ChainBase)
async def return_chain(chain_id: int, db: Session = Depends(get_db)):
    if not chain_id:
        raise HTTPException(status_code=400, detail="Chain id must be provided")

    chain = get_chain_by_id(db, chain_id)
    if not chain:
        raise HTTPException(status_code=404, detail="Chain id not found")

    chain.image = await gen_presigned_url(chain.filepath)

    return chain


@router.get("/docs/check-status", response_model=CanGrabDocs)
def can_grab_docs(token: str = Depends(verify_token), db: Session = Depends(get_db)) -> JSONResponse:
    user = get_user_from_token(db, token)

    if not user.docs_grabbed_at:
        return JSONResponse({'can_grab': True}, status_code=200)

    curr_datetime = datetime.now(timezone.utc).date()
    if curr_datetime > user.docs_grabbed_at.date():
        return JSONResponse({'can_grab': True}, status_code=200)

    return JSONResponse({'can_grab': False, 'time_left': get_time_until_midnight()}, status_code=200)


@router.patch("/docs/grab", response_model=GrabDocs)
async def grab_docs(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    try:
        can_grab_value = json.loads(can_grab_docs(token, db).body)['can_grab']
        if not can_grab_value:
            return JSONResponse({'success': False, 'detail': 'User can collect docs once a day!'}, status_code=200)

        user = get_user_from_token(db, token)
        curr_datetime = datetime.now(timezone.utc)
        last_grabbed = user.docs_grabbed_at

        if last_grabbed is None or curr_datetime.day > last_grabbed.day + 1:
            user.previous_docs_streak = user.curr_docs_streak
            user.curr_docs_streak = 1
        elif curr_datetime.day == last_grabbed.day + 1:
            user.curr_docs_streak += 1

        user.max_docs_streak = max(user.max_docs_streak, user.curr_docs_streak)
        user.docs_grabbed_at = curr_datetime
        db.commit()
        db.refresh(user)

        return JSONResponse(
            {
                'success': True,
                'detail': 'Docs grabbed!',
                'curr_docs_streak': user.curr_docs_streak,
                'previous_docs_streak': user.previous_docs_streak,
                'max_docs_streak': user.max_docs_streak,
                'time_left': get_time_until_midnight()
            },
            status_code=200
        )

    except Exception as e:
        print('Grabbing docs error:', e)
        return JSONResponse({'success': False, 'detail': 'Something went wrong while grabbing docs!'}, status_code=400)


@router.get('/users/get-online', response_model=CountUsers)
def return_online(db: Session = Depends(get_db)):
    count = calculate_24h_online(db)
    return JSONResponse({'count': count}, status_code=200)
