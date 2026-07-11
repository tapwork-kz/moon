import asyncio
import os
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

# Загружаем токен
load_dotenv("../backend/.env")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Адрес нашего запущенного FastAPI
API_URL = "http://localhost:8000"

# Создаем состояния, чтобы бот понимал, на каком мы шаге
class SwapState(StatesGroup):
    waiting_for_video = State()
    waiting_for_photo = State()

async def api_register(telegram_id: int, username: str):
    """Регистрация пользователя через наш API"""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/users/register", json={
            "telegram_id": telegram_id, 
            "username": username or "Unknown"
        }) as resp:
            data = await resp.json()
            return data["user"]["id"] # Возвращаем UUID из базы

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # Регистрируем пользователя при старте
    user_uuid = await api_register(message.from_user.id, message.from_user.username)
    
    # Сохраняем UUID в память состояния
    await state.update_data(user_uuid=user_uuid)
    
    await message.answer("Привет! Я бот для замены лиц. 🎭\n\nОтправь мне исходное видео (до 20 МБ).")
    # Переводим бота в режим ожидания видео
    await state.set_state(SwapState.waiting_for_video)

@dp.message(SwapState.waiting_for_video, F.video | F.document)
async def handle_video(message: Message, state: FSMContext):
    video = message.video or message.document
    if video.file_size > 20 * 1024 * 1024:
        return await message.answer("Файл слишком большой! Ограничение публичного API Telegram — 20 МБ.")
    
    # Сохраняем ID видео в память
    await state.update_data(video_file_id=video.file_id)
    
    await message.answer("Видео сохранено в памяти! Теперь отправь фото лица, которое нужно вставить.")
    # Переводим бота в режим ожидания фото
    await state.set_state(SwapState.waiting_for_photo)

@dp.message(SwapState.waiting_for_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    status_msg = await message.answer("Начинаю скачивание и отправку на сервер... ⏳")
    photo_file_id = message.photo[-1].file_id
    
    # Достаем данные из памяти
    data = await state.get_data()
    user_uuid = data['user_uuid']
    video_file_id = data['video_file_id']
    
    # 1. Скачиваем файлы из серверов Telegram в оперативную память
    video_file = await bot.get_file(video_file_id)
    photo_file = await bot.get_file(photo_file_id)
    
    video_io = await bot.download_file(video_file.file_path)
    photo_io = await bot.download_file(photo_file.file_path)

    # 2. Отправляем файлы в наш FastAPI бэкенд
    async with aiohttp.ClientSession() as session:
        # Отправляем видео
        v_form = aiohttp.FormData()
        v_form.add_field('user_id', user_uuid)
        v_form.add_field('file', video_io.read(), filename='video.mp4', content_type='video/mp4')
        async with session.post(f"{API_URL}/media/upload/video", data=v_form) as v_resp:
            v_data = await v_resp.json()
            db_video_id = v_data["video"]["id"]

        # Отправляем фото
        p_form = aiohttp.FormData()
        p_form.add_field('user_id', user_uuid)
        p_form.add_field('file', photo_io.read(), filename='face.jpg', content_type='image/jpeg')
        async with session.post(f"{API_URL}/media/upload/face", data=p_form) as p_resp:
            p_data = await p_resp.json()
            db_face_id = p_data["face"]["id"]

        # 3. Создаем задачу в очереди
        async with session.post(f"{API_URL}/jobs/create", json={
            "video_id": db_video_id, 
            "face_id": db_face_id
        }) as j_resp:
            j_data = await j_resp.json()

    await status_msg.edit_text(f"✅ Задача успешно создана и отправлена в очередь GPU!\n\nID задачи: `{j_data['job']['id']}`\n\nОжидайте, скоро пришлю результат.")
    
    # Очищаем состояние, чтобы пользователь мог загрузить новое видео
    await state.clear()

async def main():
    print("🤖 Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())