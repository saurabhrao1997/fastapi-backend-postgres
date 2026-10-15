from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate,UserResponse



def get_user(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    normalized_email = email.strip().lower()
    return db.scalar(select(User).where(User.email == normalized_email))


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


def create_user(db: Session, payload: UserCreate) -> UserResponse:
    user = User(
        full_name=payload.full_name.strip(),
        email=str(payload.email).strip().lower(),
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("An account with this email already exists.") from error
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user: User,
    payload: UserUpdate,
    *,
    allow_role_change: bool = False,
) -> User:
    changes = payload.model_dump(exclude_unset=True)
    if "email" in changes and changes["email"] is not None:
        changes["email"] = str(changes["email"]).strip().lower()
    if "full_name" in changes and changes["full_name"] is not None:
        changes["full_name"] = changes["full_name"].strip()
    if "password" in changes and changes["password"] is not None:
        changes["hashed_password"] = hash_password(changes.pop("password"))
    if not allow_role_change:
        changes.pop("role", None)

    for field, value in changes.items():
        setattr(user, field, value)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("An account with this email already exists.") from error
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
