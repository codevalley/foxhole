from pydantic import BaseModel, Field
from typing import List


class FileUploadResponse(BaseModel):
    """Response model for successful file uploads."""

    message: str = Field(..., description="Success message.")
    object_name: str = Field(..., description="Name of the uploaded object.")


class FileURLResponse(BaseModel):
    """Response model for file URL retrieval."""

    url: str = Field(..., description="URL of the requested file.")


class FileListResponse(BaseModel):
    """Response model for listing files."""

    files: List[str] = Field(..., description="List of file names.")
