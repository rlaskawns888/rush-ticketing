from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db_session
from app.models import User
 

router = APIRouter(
    prefix="/auth", tags=["auth"]
)


class SignupRequest(BaseModel):
    username: str
    password: str
    name: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/signup")
async def signup(body: SignupRequest, session: AsyncSession = Depends(get_db_session)):
    existing = await session.scalar(select(User).where(User.username == body.username))

    if existing:
        raise HTTPException(status_code=409, detail="이미 사용 중인 아이디예요.")
    
    user = User(
        username = body.username,
        password_hash = hash_password(body.password),
        name=body.name,
    )
    session.add(user)
    await session.commit()

    return {"username": user.username, "name": user.name}


@router.post("/login")
async def login(body: LoginRequest, session: AsyncSession = Depends(get_db_session)):
    user = await session.scalar(select(User).where(User.username == body.username))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않아요.")
    
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer", "name": user.name}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "name": current_user.name}