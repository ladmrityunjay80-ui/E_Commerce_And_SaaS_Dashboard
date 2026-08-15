import os
import boto3
from typing import Optional
from app.core.config import settings


class StorageService:
    def __init__(self):
        self.use_s3 = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.AWS_S3_BUCKET)
        self.use_cloudinary = bool(settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET)
        
        if self.use_s3:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket = settings.AWS_S3_BUCKET
        
        if self.use_cloudinary:
            try:
                import cloudinary
                cloudinary.config(
                    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                    api_key=settings.CLOUDINARY_API_KEY,
                    api_secret=settings.CLOUDINARY_API_SECRET
                )
                self.cloudinary = cloudinary
            except ImportError:
                self.use_cloudinary = False

    async def upload_file(self, file_data: bytes, filename: str, content_type: str = 'image/jpeg') -> str:
        """Upload file to storage and return URL."""
        if self.use_s3:
            return await self._upload_to_s3(file_data, filename, content_type)
        elif self.use_cloudinary:
            return await self._upload_to_cloudinary(file_data, filename, content_type)
        else:
            raise ValueError("No storage service configured")

    async def _upload_to_s3(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Upload file to AWS S3."""
        try:
            key = f"uploads/{filename}"
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_data,
                ContentType=content_type,
                ACL='public-read'
            )
            return f"https://{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
        except Exception as e:
            raise Exception(f"S3 upload failed: {str(e)}")

    async def _upload_to_cloudinary(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Upload file to Cloudinary."""
        try:
            import io
            import cloudinary.uploader
            
            # Convert bytes to file-like object
            file_like = io.BytesIO(file_data)
            
            result = cloudinary.uploader.upload(
                file_like,
                resource_type="auto",
                public_id=f"uploads/{filename}",
                format=filename.split('.')[-1] if '.' in filename else 'jpg'
            )
            return result['secure_url']
        except Exception as e:
            raise Exception(f"Cloudinary upload failed: {str(e)}")

    async def delete_file(self, file_url: str) -> bool:
        """Delete file from storage."""
        if self.use_s3 and 'amazonaws.com' in file_url:
            return await self._delete_from_s3(file_url)
        elif self.use_cloudinary and 'cloudinary.com' in file_url:
            return await self._delete_from_cloudinary(file_url)
        return False

    async def _delete_from_s3(self, file_url: str) -> bool:
        """Delete file from AWS S3."""
        try:
            key = file_url.split(f'/{self.bucket}/')[-1]
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception as e:
            print(f"S3 delete failed: {str(e)}")
            return False

    async def _delete_from_cloudinary(self, file_url: str) -> bool:
        """Delete file from Cloudinary."""
        try:
            import cloudinary.api
            public_id = file_url.split('/')[-1].split('.')[0]
            cloudinary.api.delete_resources([f"uploads/{public_id}"], resource_type="auto")
            return True
        except Exception as e:
            print(f"Cloudinary delete failed: {str(e)}")
            return False

    def get_storage_type(self) -> str:
        """Return the active storage type."""
        if self.use_s3:
            return "s3"
        elif self.use_cloudinary:
            return "cloudinary"
        return "none"
