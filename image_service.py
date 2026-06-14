import io
import logging
import uuid
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from config import Config as AppConfig
from yandex_vision import YandexVision

logger = logging.getLogger(__name__)


class ImageService:

    def __init__(self, config: AppConfig, vision: YandexVision):
        self.config = config
        self.vision = vision
        self._s3 = None

    def _get_s3(self):
        if self._s3 is not None:
            return self._s3
        if self.config.yandex_static_key_id and self.config.yandex_static_key:
            session = boto3.session.Session()
            self._s3 = session.client(
                "s3",
                endpoint_url="https://storage.yandexcloud.net",
                aws_access_key_id=self.config.yandex_static_key_id,
                aws_secret_access_key=self.config.yandex_static_key,
                config=Config(signature_version="s3v4"),
                region_name="ru-central1",
            )
        return self._s3

    async def download_photo(self, bot, file_id: str) -> bytes:
        file = await bot.get_file(file_id)
        buffer = io.BytesIO()
        await bot.download_file(file.file_path, buffer)
        return buffer.getvalue()

    async def upload_to_storage(self, image_bytes: bytes, filename: Optional[str] = None) -> str:
        if filename is None:
            filename = f"rooms/{uuid.uuid4()}.jpg"

        s3 = self._get_s3()
        if s3 is None:
            logger.warning("S3 не настроен, сохраняем локально")
            local_path = f"storage/{filename}"
            import aiofiles
            async with aiofiles.open(local_path, "wb") as f:
                await f.write(image_bytes)
            return local_path

        try:
            s3.put_object(
                Bucket=self.config.yandex_bucket_name,
                Key=filename,
                Body=image_bytes,
                ContentType="image/jpeg",
                ACL="public-read",
            )
            return f"https://{self.config.yandex_bucket_name}.storage.yandexcloud.net/{filename}"
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise

    async def analyze_photo(self, image_bytes: bytes) -> str:
        return await self.vision.analyze_image(image_bytes)

    async def process_room_photo(self, bot, file_id: str) -> dict:
        image_bytes = await self.download_photo(bot, file_id)
        photo_url = await self.upload_to_storage(image_bytes)
        description = await self.analyze_photo(image_bytes)
        return {
            "photo_url": photo_url,
            "description": description,
            "image_bytes": image_bytes,
        }
