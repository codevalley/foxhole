from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.services.storage_service import StorageService
from app.dependencies import get_storage_service, get_current_user
from app.models import User
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: User = Depends(get_current_user),
) -> dict:
    logger.debug(f"Received file upload request: {file.filename}")
    logger.debug(f"Current user: {current_user.id}")
    logger.debug(f"Storage service type: {type(storage_service).__name__}")
    try:
        logger.debug("Attempting to upload file")
        object_name = await storage_service.upload_file(
            file, "default-bucket", file.filename
        )
        if object_name:
            logger.info(f"File uploaded successfully: {object_name}")
            return {"message": "File uploaded successfully", "object_name": object_name}
        else:
            logger.error("File upload failed")
            raise HTTPException(status_code=500, detail="Failed to upload file")
    except Exception as e:
        logger.exception(f"Failed to upload file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/file/{object_name}")
async def get_file_url(
    object_name: str,
    storage_service: StorageService = Depends(get_storage_service),
    current_user: User = Depends(get_current_user),
) -> dict:
    url = await storage_service.get_file_url("default-bucket", object_name)
    if url:
        return {"url": url}
    raise HTTPException(status_code=404, detail="File not found")


@router.get("/")
async def list_files(
    storage_service: StorageService = Depends(get_storage_service),
    current_user: User = Depends(get_current_user),
) -> dict[str, List[str]]:
    files = await storage_service.list_files("default-bucket")
    if not files:
        logger.info("No files found or error occurred while listing files")
    return {"files": files}
