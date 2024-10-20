from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict


class PersonContact(BaseModel):
    email: str
    phone: str


class PersonBase(BaseModel):
    name: str
    designation: str
    relation_type: str
    importance: Literal["high", "medium", "low"]
    notes: str
    contact: PersonContact


class PersonCreate(PersonBase):
    person_id: str
    importance: Literal["high", "medium", "low"] = Field(
        ..., pattern="^(high|medium|low)$"
    )


class Person(PersonBase):
    person_id: str

    class Config:
        from_attributes = True


class TaskPeople(BaseModel):
    owner: str
    final_beneficiary: str
    stakeholders: List[str]


class TaskBase(BaseModel):
    type: Literal["1", "2", "3", "4"]
    description: str
    status: Literal["active", "pending", "completed"]
    actions: List[str]
    people: TaskPeople
    dependencies: List[str]
    schedule: str
    priority: Literal["high", "medium", "low"]


class TaskCreate(TaskBase):
    task_id: str


class Task(TaskBase):
    task_id: str

    class Config:
        from_attributes = True


class TopicBase(BaseModel):
    name: str
    description: str
    keywords: List[str]
    related_people: List[str]
    related_tasks: List[str]


class TopicCreate(TopicBase):
    topic_id: str


class Topic(TopicBase):
    topic_id: str

    class Config:
        from_attributes = True


class NoteBase(BaseModel):
    content: str
    created_at: str
    updated_at: str
    related_people: List[str]
    related_tasks: List[str]
    related_topics: List[str]


class NoteCreate(NoteBase):
    note_id: str


class Note(NoteBase):
    note_id: str

    class Config:
        from_attributes = True


class AffectedEntities(BaseModel):
    tasks: List[str] = Field(default_factory=list)
    people: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class Instructions(BaseModel):
    status: Literal["incomplete", "complete"]
    followup: str
    new_prompt: str
    write: bool
    affected_entities: AffectedEntities


class Data(BaseModel):
    tasks: List[Task] = Field(default_factory=list)
    people: List[Person] = Field(default_factory=list)
    topics: List[Topic] = Field(default_factory=list)
    notes: List[Note] = Field(default_factory=list)


class LLMResponse(BaseModel):
    instructions: Instructions
    data: Data


class SidekickThreadCreate(BaseModel):
    user_id: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)


class SidekickThreadResponse(BaseModel):
    id: str
    user_id: str
    conversation_history: List[Dict[str, str]]

    class Config:
        from_attributes = True


class SidekickInput(BaseModel):
    user_input: str
    thread_id: Optional[str] = None


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class SidekickOutput(BaseModel):
    response: str
    thread_id: str
    new_prompt: Optional[str] = None
    is_thread_complete: bool
    updated_entities: Dict[str, int]
    status: Literal["incomplete", "complete"]
    token_usage: TokenUsage
