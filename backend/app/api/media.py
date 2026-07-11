from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.storage import storage_service
from app.services.database import create_video_record, create_face_record
import uuid

router = APIRouter(prefix="/media", tags=["Media Upload"])

@router.post("/upload/video")
async def upload_video(user_id: str = Form(...), file: UploadFile = File(...)):
    if not file.filename.endswith(('.mp4', '.mov', '.avi')):
        raise HTTPException(status_code=400, detail="Invalid video format")
    
    # Генерируем уникальное имя файла
    file_ext = file.filename.split('.')[-1]
    file_path = f"{user_id}/{uuid.uuid4()}.{file_ext}"
    
    file_bytes = await file.read()
    
    # Загружаем в Supabase Storage
    public_url = await storage_service.upload_file("videos-input", file_path, file_bytes, file.content_type)
    
    # Создаем запись в БД
    video_record = create_video_record(user_id, public_url)
    
    return {"status": "success", "video": video_record}

@router.post("/upload/face")
async def upload_face(user_id: str = Form(...), file: UploadFile = File(...)):
    if not file.filename.endswith(('.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Invalid image format")
    
    file_ext = file.filename.split('.')[-1]
    file_path = f"{user_id}/{uuid.uuid4()}.{file_ext}"
    
    file_bytes = await file.read()
    public_url = await storage_service.upload_file("faces", file_path, file_bytes, file.content_type)
    
    face_record = create_face_record(user_id, public_url)
    
    return {"status": "success", "face": face_record}