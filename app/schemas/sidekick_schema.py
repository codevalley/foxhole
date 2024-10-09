from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class SidekickThreadCreate(BaseModel):
    user_id: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)


class SidekickThreadResponse(BaseModel):
    id: str
    user_id: str
    conversation_history: List[Dict[str, str]]

    class Config:
        from_attributes = True


class SidekickContextCreate(BaseModel):
    user_id: str
    context_type: str
    data: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class SidekickContextResponse(BaseModel):
    id: str
    user_id: str
    context_type: str
    data: Dict[str, Any]

    class Config:
        from_attributes = True


class SidekickInput(BaseModel):
    user_input: str
    thread_id: Optional[str] = None


class SidekickOutput(BaseModel):
    response: str
    thread_id: str
    status: str
    primary_type: str
    new_prompt: Optional[str] = None
    is_thread_complete: bool
    updated_entities: Dict[str, int]
