"""
OpenAI function definitions for Sidekick V2.
These schemas define the interface between OpenAI and our database operations.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class PersonSearchParams(BaseModel):
    """Parameters for searching people"""

    name: Optional[str] = Field(None, description="Name or part of name to search for")
    designation: Optional[str] = Field(None, description="Filter by designation")
    relation_type: Optional[str] = Field(None, description="Filter by relation type")
    importance: Optional[Literal["high", "medium", "low"]] = Field(
        None, description="Filter by importance level"
    )


class TaskSearchParams(BaseModel):
    """Parameters for searching tasks"""

    query: Optional[str] = Field(
        None, description="Free text search in task description"
    )
    type: Optional[Literal["1", "2", "3", "4"]] = Field(
        None, description="Filter by task type"
    )
    status: Optional[Literal["active", "pending", "completed"]] = Field(
        None, description="Filter by task status"
    )
    priority: Optional[Literal["high", "medium", "low"]] = Field(
        None, description="Filter by priority level"
    )
    owner: Optional[str] = Field(None, description="Filter by task owner")


class TopicSearchParams(BaseModel):
    """Parameters for searching topics"""

    keyword: Optional[str] = Field(None, description="Search in topic keywords")
    name: Optional[str] = Field(None, description="Search in topic name")
    description: Optional[str] = Field(None, description="Search in topic description")
    related_person: Optional[str] = Field(None, description="Filter by related person")


class NoteSearchParams(BaseModel):
    """Parameters for searching notes"""

    query: Optional[str] = Field(None, description="Free text search in note content")
    related_topic: Optional[str] = Field(None, description="Filter by related topic")
    related_person: Optional[str] = Field(None, description="Filter by related person")
    related_task: Optional[str] = Field(None, description="Filter by related task")


# OpenAI Function Definitions
FUNCTION_DEFINITIONS = [
    {
        "name": "get_people",
        "description": "Search for people in the system based on various criteria",
        "parameters": PersonSearchParams.model_json_schema(),
    },
    {
        "name": "get_tasks",
        "description": "Search for tasks based on various criteria",
        "parameters": TaskSearchParams.model_json_schema(),
    },
    {
        "name": "get_topics",
        "description": "Search for topics based on keywords or related entities",
        "parameters": TopicSearchParams.model_json_schema(),
    },
    {
        "name": "get_notes",
        "description": "Search for notes based on content or related entities",
        "parameters": NoteSearchParams.model_json_schema(),
    },
]


# Function Response Types (for type hints in handlers)
class PersonResponse(BaseModel):
    """Response format for person search"""

    results: List[Dict[str, Any]]
    total: int


class TaskResponse(BaseModel):
    """Response format for task search"""

    results: List[Dict[str, Any]]
    total: int


class TopicResponse(BaseModel):
    """Response format for topic search"""

    results: List[Dict[str, Any]]
    total: int


class NoteResponse(BaseModel):
    """Response format for note search"""

    results: List[Dict[str, Any]]
    total: int
