from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    database_status: str
