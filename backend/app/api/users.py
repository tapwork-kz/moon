from fastapi import APIRouter
from pydantic import BaseModel
from app.services.database import get_or_create_user

router = APIRouter(prefix="/users", tags=["Users"])

class UserCreate(BaseModel):
    telegram_id: int
    username: str | None = None

@router.post("/register")
def register_user(user: UserCreate):
    db_user = get_or_create_user(user.telegram_id, user.username)
    return {"status": "success", "user": db_user}