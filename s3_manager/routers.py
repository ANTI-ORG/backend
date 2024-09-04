import base64

import aioboto3
from botocore.exceptions import NoCredentialsError
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import verify_token
from app.utils import get_user_from_token
from s3_manager.file_operations import validate_file, resize_image
from s3_manager.aws_s3_config import BUCKET_NAME, config, create_s3_client
from admin.dependencies import is_admin
from app import models

file_router = APIRouter()


def get_class_dir_name(model_class) -> str:
    class_name = model_class.__name__
    return f"image/{class_name.lower()}/"


# Виртуальные пути для хранения файлов на AWS S3
FILE_PATHS = {
    'avatar': {
        'dirname': 'image/avatar/',
        'class': models.User,
        'size': [
            (256, 256),
            (128, 128)
        ]
    },
    'project': {
        'dirname': get_class_dir_name(models.Project),
        'class': models.Project,
        'size': [
            (32, 32),
            (64, 64)
        ]
    },
    'chain': {
        'dirname': get_class_dir_name(models.Chain),
        'class': models.Chain,
        'size': [
            (32, 32),
            (64, 64)
        ]
    },
    'quest': {
        'dirname': get_class_dir_name(models.Quest),
        'class': models.Quest,
        'size': [
            (512, 256)
        ]
    },
    'task': {
        'dirname': get_class_dir_name(models.Task),
        'class': models.Task,
        'size': [
            (128, 128)
        ]
    }
}

MAX_FILE_SIZE = 1 * 1024 * 1024

SUPPORTED_FILE_TYPES = {
    'image/png': 'png',
    'image/jpeg': 'jpeg'
}

# Создание клиента S3 с использованием aioboto3
session = aioboto3.Session()
bucket = BUCKET_NAME


async def s3_upload(contents: bytes, key: str):
    print(f'Uploading file {key} to s3')
    async with create_s3_client() as client:
        try:
            await client.put_object(Body=contents, Bucket=bucket, Key=key)
        except Exception as e:
            raise HTTPException(status_code=500, detail='Failed to upload file')


async def s3_delete(key: str):
    print(f'Deleting file {key} from s3')
    async with create_s3_client() as client:
        try:
            await client.delete_objects(Bucket=bucket, Delete={'Objects': [{'Key': key}]})
        except Exception as e:
            raise HTTPException(status_code=500, detail='Failed to delete old file')


async def s3_delete_old_files(prefix: str):
    async with create_s3_client() as client:
        response = await client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if 'Contents' in response:
            for obj in response['Contents']:
                await s3_delete(obj['Key'])


async def s3_download(key: str) -> bytes:
    print(f'Downloading file {key} from s3')
    async with create_s3_client() as client:
        try:
            response = await client.get_object(Bucket=BUCKET_NAME, Key=key)
            async with response['Body'] as stream:
                contents = await stream.read()
            return contents
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail='Failed to download file:')


async def gen_presigned_url(filepath, expiration=60):
    async with create_s3_client() as client:
        try:
            response = await client.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': filepath},
                ExpiresIn=expiration
            )
            return response
        except NoCredentialsError:
            print("Ошибка: Неверные учетные данные AWS")
            return None


async def upload_avatar_on_s3(base64_image: str, token: str = Depends(verify_token),
                              db: Session = Depends(get_db)):
    try:
        image_data = base64.b64decode(base64_image)
        file_type = validate_file(image_data, MAX_FILE_SIZE, SUPPORTED_FILE_TYPES)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail='Something went wrong with file data.')

    user = get_user_from_token(db, token)
    file_path_no_extension = FILE_PATHS['avatar']['dirname'] + user.id

    await s3_delete_old_files(file_path_no_extension)

    resized_contents = resize_image(image_data, SUPPORTED_FILE_TYPES[file_type], FILE_PATHS['avatar']['size'])

    full_path = file_path_no_extension + '.' + SUPPORTED_FILE_TYPES[file_type]

    try:
        await s3_upload(contents=resized_contents,
                        key=full_path)

        user.filepath = full_path
        db.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail='Something went wrong.')

    return JSONResponse(status_code=200, content={"message": "File uploaded successfully"})


@file_router.post("/upload/any/{file_dir}/{id}")  # Роут только для админов!
async def upload_any_on_s3(file_dir: str, id: str, file: UploadFile = File(...), db: Session = Depends(get_db),
                           have_access: bool = Depends(is_admin)):
    contents = await file.read()
    file_type = validate_file(contents, MAX_FILE_SIZE, SUPPORTED_FILE_TYPES)

    if file_dir not in FILE_PATHS.keys():
        raise HTTPException(status_code=400, detail='Available file dirs are: {}'.format(FILE_PATHS.keys()))

    id = str(id)
    file_path_no_extension = FILE_PATHS[file_dir]['dirname'] + id

    await s3_delete_old_files(file_path_no_extension)

    resized_contents = resize_image(contents, SUPPORTED_FILE_TYPES[file_type], FILE_PATHS[file_dir]['size'])

    full_path = file_path_no_extension + '.' + SUPPORTED_FILE_TYPES[file_type]

    try:
        await s3_upload(contents=resized_contents,
                        key=full_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail='Something went while file uploading wrong.')

    obj_class = FILE_PATHS[file_dir]['class']

    id = int(id) if id.isdigit() else id

    found_object = db.query(obj_class).filter(obj_class.id == id).first()

    if not found_object:
        raise HTTPException(status_code=400,
                            detail='Object "{}" with id={} not found'.format(file_dir, id))

    found_object.filepath = full_path
    db.commit()

    return full_path
