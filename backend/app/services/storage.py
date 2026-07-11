import os
from urllib.parse import urlparse
from supabase import create_client, Client
from app.config import settings

class StorageService:
    def __init__(self):
        self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    async def upload_file(self, bucket_name: str, file_path: str, file_bytes: bytes, content_type: str) -> str:
        """Загружает файл в указанный бакет и возвращает публичную ссылку"""
        # Отправляем файл в Supabase Storage
        self.supabase.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": content_type, "x-upsert": "true"}
        )
        # Получаем публичный URL
        public_url = self.supabase.storage.from_(bucket_name).get_public_url(file_path)
        return public_url

    async def delete_file_by_url(self, public_url: str) -> bool:
        """Автоматически извлекает бакет и имя файла из URL и удаляет его"""
        try:
            # Пример URL: https://xyz.supabase.co/storage/v1/object/public/videos-input/user_123/video.mp4
            parsed_url = urlparse(public_url)
            path_parts = parsed_url.path.split('/')
            
            # Индексы зависят от структуры URL Supabase:
            # /storage/v1/object/public/[bucket_name]/[file_path...]
            if "public" in path_parts:
                public_index = path_parts.index("public")
                bucket_name = path_parts[public_index + 1]
                file_path = "/".join(path_parts[public_index + 2:])
                
                # Удаляем файл из бакета
                self.supabase.storage.from_(bucket_name).remove([file_path])
                return True
            return False
        except Exception as e:
            print(f"Ошибка при удалении файла {public_url}: {e}")
            return False

storage_service = StorageService()