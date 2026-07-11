from fastapi import FastAPI
from app.api import users, media
from app.config import settings

app = FastAPI(
    title="Telegram AI Face Swap Bot API",
    version="1.0.0"
)

# Подключаем роутеры
app.include_router(users.router)
app.include_router(media.router)

@app.get("/")
def read_root():
    return {"status": "running", "message": "Face Swap API работает!"}

from fastapi import FastAPI
from app.api import users, media, jobs # Добавили jobs
from app.config import settings

app = FastAPI(
    title="Telegram AI Face Swap Bot API",
    version="1.0.0"
)

app.include_router(users.router)
app.include_router(media.router)
app.include_router(jobs.router) # Подключили роутер

@app.get("/")
def read_root():
    return {"status": "running", "message": "Face Swap API работает!"}