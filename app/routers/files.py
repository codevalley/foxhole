from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.services.storage_service import StorageService
from app.dependencies import get_storage_service, get_current_user
from app.models import User
from app.schemas.file_schema import (
    FileUploadResponse,
    FileURLResponse,
    FileListResponse,
)
import logging
from app.core.exceptions import DatabaseOperationError


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: User = Depends(get_current_user),
) -> FileUploadResponse:
    """
    Upload a file to the storage service.
    """
    logger.info(f"User {current_user.id} is attempting to upload file: {file.filename}")
    try:
        logger.debug("Attempting to upload file")
        object_name = await storage_service.upload_file(
            file, "default-bucket", file.filename
        )
        if object_name:
            logger.info(
                f"File uploaded successfully by user {current_user.id}: {object_name}"
            )
            return FileUploadResponse(
                message="File uploaded successfully", object_name=object_name
            )
        else:
            logger.error(f"File upload failed for user {current_user.id}")
            raise DatabaseOperationError("Failed to upload file")
    except DatabaseOperationError as e:
        logger.exception(f"Database operation error during file upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")
    except Exception as e:
        logger.exception(f"Unexpected error during file upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/file/{object_name}", response_model=FileURLResponse)
async def get_file_url(
    object_name: str,
    storage_service: StorageService = Depends(get_storage_service),
    current_user: User = Depends(get_current_user),
) -> FileURLResponse:
    """
    Retrieve the URL of a specific file.
    """
    logger.info(f"User {current_user.id} is requesting URL for file: {object_name}")
    try:
        url = await storage_service.get_file_url("default-bucket", object_name)
        if url:
            logger.info(
                f"File URL retrieved successfully for user {current_user.id}: {object_name}"
            )
            return FileURLResponse(url=url)
        else:
            logger.warning(f"File not found for user {current_user.id}: {object_name}")
            raise HTTPException(status_code=404, detail="File not found")
    except HTTPException:
        # Re-raise HTTP exceptions (including our 404)
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during file URL retrieval: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve file URL: {str(e)}"
        )


@router.get("/", response_model=FileListResponse)
async def list_files(
    storage_service: StorageService = Depends(get_storage_service),
    current_user: User = Depends(get_current_user),
) -> FileListResponse:
    """
    List all files in the storage bucket.
    """
    logger.info(f"User {current_user.id} is requesting list of files")
    try:
        files = await storage_service.list_files("default-bucket")
        if not files:
            logger.info(f"No files found for user {current_user.id} in bucket.")
        else:
            logger.info(f"User {current_user.id} retrieved list of files: {files}")
        return FileListResponse(files=files)
    except Exception as e:
        logger.exception(f"Unexpected error during listing files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")
