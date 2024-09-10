from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.services.storage_service import StorageService
from app.dependencies import get_storage_service, get_current_user
from app.models import User
from typing import Dict, List, Any
import uuid

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    # Generate a unique filename if the original filename is None
    object_name = file.filename or f"upload_{uuid.uuid4().hex}"
    uploaded_object_name = await storage_service.upload_file(
        file, "default-bucket", object_name
    )
    return {
        "message": "File uploaded successfully",
        "object_name": uploaded_object_name,
        "uploaded_by": current_user.id,  # Use user's id (handle) here
    }


@router.get("/file/{object_name}")
async def get_file_url(
    object_name: str, storage_service: StorageService = Depends(get_storage_service)
) -> Dict[str, str]:
    url = await storage_service.get_file_url("default-bucket", object_name)
    if url is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {"url": url}


@router.get("/")
async def list_files(
    storage_service: StorageService = Depends(get_storage_service),
    current_user: User = Depends(get_current_user),
) -> dict[str, List[str]]:
    files = await storage_service.list_files("default-bucket")
    return {"files": files}
