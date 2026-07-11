from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from app.services.database import create_job_record
from app.services.ai_worker import process_face_swap

router = APIRouter(prefix="/jobs", tags=["Jobs"])

class JobCreate(BaseModel):
    video_id: str
    face_id: str

@router.post("/create")
def create_job(job: JobCreate, background_tasks: BackgroundTasks):
    # 1. Создаем запись в таблице jobs в Supabase
    new_job = create_job_record(job.video_id, job.face_id)
    job_id = new_job["id"]
    
    # 2. Отправляем запрос в RunPod в фоновом режиме (Celery больше не нужен!)
    background_tasks.add_task(process_face_swap, job_id, job.video_id, job.face_id)
    
    return {"status": "success", "job": new_job, "message": "Задача отправлена в Serverless облако"}