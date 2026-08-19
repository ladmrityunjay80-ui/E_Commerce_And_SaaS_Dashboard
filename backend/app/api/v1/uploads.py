from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.storage import StorageService
from app.api.deps import get_current_user
from app.models.user import User as UserModel
from app.core.rbac import has_permission

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file to the configured storage provider."""
    if not has_permission(current_user, "users:update"):
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        contents = await file.read()
        storage = StorageService()
        url = await storage.upload_file(
            file_data=contents,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
        )
        return {
            "url": url,
            "filename": file.filename,
            "content_type": file.content_type,
            "storage": storage.get_storage_type(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
