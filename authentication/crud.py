from sqlalchemy.orm import Session

from app import models
from authentication.auth import validate_token


def delete_expired_tokens(db: Session):
    tokens = db.query(models.Token).all()
    for token in tokens:
        if not validate_token(db, token.access_token):
            db.delete(token)
    db.commit()
