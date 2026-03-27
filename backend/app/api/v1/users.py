import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.models.user import User
from app.schemas.auth import UserMe
from app.services.auth_service import create_user
from app.utils.exceptions import NotFoundError


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "agent"


router = APIRouter()


@router.post("", response_model=UserMe, status_code=201)
async def create_new_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user=Depends(require_roles("super_admin", "admin")),
):
    user = await create_user(
        db,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        role=body.role,
        tenant_id=tenant_id,
    )
    return UserMe(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
    )


@router.get("", response_model=list[UserMe])
async def list_users(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager")),
):
    result = await db.execute(
        select(User).where(User.tenant_id == tenant_id, User.is_active)
    )
    users = result.scalars().all()
    return [
        UserMe(
            id=str(u.id),
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            tenant_id=str(u.tenant_id) if u.tenant_id else None,
        )
        for u in users
    ]


@router.delete("/{user_id}", status_code=204)
async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
):
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("Usuário")
    user.is_active = False
