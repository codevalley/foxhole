from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.services.storage_service import StorageService
from app.dependencies import get_storage_service
from typing import Dict, Any

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    storage_service: StorageService = Depends(get_storage_service),
) -> Dict[str, Any]:
    """
    Upload a file to the storage service.

    Args:
        file (UploadFile): The file to be uploaded.
        storage_service (StorageService): The storage service to use.

    Returns:
        dict: A dictionary containing the upload result.
    """
    bucket_name = "my-bucket"
    object_name = f"uploads/{file.filename}"
    result = await storage_service.upload_file(file, bucket_name, object_name)
    if result:
        return {"message": "File uploaded successfully", "object_name": result}
    raise HTTPException(status_code=500, detail="Failed to upload file")


@router.get("/file/{object_name}")
async def get_file_url(
    object_name: str, storage_service: StorageService = Depends(get_storage_service)
) -> Dict[str, str]:
    """
    Get the URL for a file in the storage service.

    Args:
        object_name (str): The name of the object to retrieve.
        storage_service (StorageService): The storage service to use.

    Returns:
        dict: A dictionary containing the file URL or an error message.
    """
    bucket_name = "my-bucket"
    url = await storage_service.get_file_url(bucket_name, object_name)
    if url:
        return {"url": url}
    raise HTTPException(status_code=404, detail="File not found")


@router.get("/")
async def list_files(
    storage_service: StorageService = Depends(get_storage_service),
) -> Dict[str, Any]:
    """
    List all files in the default bucket.

    Args:
        storage_service (StorageService): The storage service to use.

    Returns:
        dict: A dictionary containing the list of files.
    """
    bucket_name = "my-bucket"
    files = await storage_service.list_files(bucket_name)
    return {"files": files}
