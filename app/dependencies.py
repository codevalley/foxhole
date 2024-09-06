from app.services.storage_service import MinioStorageService

# Create a single instance of MinioStorageService
minio_service = MinioStorageService()

def get_storage_service():
    """
    Dependency function to get the storage service.
    Returns the MinioStorageService instance.
    """
    return minio_service