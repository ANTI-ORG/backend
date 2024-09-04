from fastapi import HTTPException, status
from sqlalchemy.orm import Session


def get_object_or_404(model, db: Session, **kwargs):
    obj = db.query(model).filter_by(**kwargs).first()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found")
    return obj