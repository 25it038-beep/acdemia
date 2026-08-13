from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from app.models.models import UserRole, LearningMode


class UserCreate(BaseModel):
    email: str
    username: str
    full_name: str
    password: str
    role: UserRole = UserRole.STUDENT
    university: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[int] = None
    education_level: Optional[str] = None
    occupation: Optional[str] = None
    domain: Optional[str] = None
    learning_mode: LearningMode = LearningMode.COLLEGE


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    university: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[int] = None
    education_level: Optional[str] = None
    occupation: Optional[str] = None
    domain: Optional[str] = None
    learning_mode: Optional[LearningMode] = None


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: str
    role: UserRole
    avatar_url: Optional[str] = None
    university: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[int] = None
    education_level: Optional[str] = None
    occupation: Optional[str] = None
    domain: Optional[str] = None
    learning_mode: LearningMode
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SubjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    university: Optional[str] = None
    semester: Optional[int] = None
    subject_code: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    syllabus: Optional[dict] = None


class SubjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    university: Optional[str] = None
    semester: Optional[int] = None
    subject_code: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    progress: float = 0.0
    unit_count: int = 0
    file_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class UnitCreate(BaseModel):
    name: str
    description: Optional[str] = None
    order: int = 0


class UnitResponse(BaseModel):
    id: UUID
    subject_id: UUID
    name: str
    description: Optional[str] = None
    order: int
    chapter_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ChapterCreate(BaseModel):
    name: str
    description: Optional[str] = None
    order: int = 0
    estimated_hours: float = 1.0
    difficulty: int = 1


class ChapterResponse(BaseModel):
    id: UUID
    unit_id: UUID
    name: str
    description: Optional[str] = None
    order: int
    estimated_hours: float
    difficulty: int
    topic_count: int = 0
    progress: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True


class TopicCreate(BaseModel):
    name: str
    content: Optional[str] = None
    order: int = 0
    difficulty: int = 1
    importance: int = 5
    prerequisites: List[str] = []
    tags: List[str] = []


class TopicResponse(BaseModel):
    id: UUID
    chapter_id: UUID
    name: str
    content: Optional[str] = None
    summary: Optional[str] = None
    order: int
    difficulty: int
    importance: int
    prerequisites: List[str]
    tags: List[str]
    concept_count: int = 0
    progress: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True


class ConceptCreate(BaseModel):
    name: str
    explanation: Optional[str] = None
    definition: Optional[str] = None
    formula: Optional[str] = None
    code_example: Optional[str] = None
    analogy: Optional[str] = None
    examples: List[Any] = []
    difficulty: int = 1
    importance: int = 5
    parent_concept_id: Optional[UUID] = None


class ConceptResponse(BaseModel):
    id: UUID
    topic_id: UUID
    name: str
    explanation: Optional[str] = None
    definition: Optional[str] = None
    formula: Optional[str] = None
    code_example: Optional[str] = None
    analogy: Optional[str] = None
    difficulty: int
    importance: int
    exam_frequency: int
    created_at: datetime

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    id: UUID
    original_filename: str
    file_type: str
    file_size: int
    status: str
    pages: int
    chunks: int
    subject_id: Optional[UUID] = None
    content_preview: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class QuizCreate(BaseModel):
    topic_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    title: str
    quiz_type: str = "mcq"
    difficulty: str = "medium"
    time_limit_minutes: Optional[int] = None
    question_count: int = 10


class QuizResponse(BaseModel):
    id: UUID
    title: str
    quiz_type: str
    difficulty: str
    total_questions: int
    score: Optional[float] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    id: UUID
    question_text: str
    question_type: str
    options: Optional[list] = None
    difficulty: int
    marks: int

    class Config:
        from_attributes = True


class QuizSubmission(BaseModel):
    answers: List[dict]


class ChatMessage(BaseModel):
    session_id: str
    message: str
    mode: str = "tutor"
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    chapter_id: Optional[UUID] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    metadata: Optional[dict] = None


class ChatMessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatSessionSummary(BaseModel):
    session_id: str
    first_message: str
    message_count: int
    last_updated: Optional[datetime] = None


class StudyPlanRequest(BaseModel):
    title: str
    description: Optional[str] = None
    exam_date: Optional[datetime] = None
    daily_hours: float = 2.0
    subjects: List[UUID] = []


class WhiteboardCreate(BaseModel):
    name: str = "Untitled"


class WhiteboardUpdate(BaseModel):
    name: Optional[str] = None
    elements: Optional[list] = None


class FlashcardCreate(BaseModel):
    topic_id: Optional[UUID] = None
    front: str
    back: str


class FlashcardGenerate(BaseModel):
    subject_id: UUID
    count: int = 10


class StudySessionStart(BaseModel):
    subject_id: Optional[UUID] = None
    session_type: str = "study"


class MemoryResponse(BaseModel):
    id: UUID
    memory_type: str
    content: str
    context: Optional[str] = None
    importance: int
    recall_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeGraphResponse(BaseModel):
    nodes: list
    edges: list


class WorkflowResponse(BaseModel):
    nodes: list
    edges: list
    workflow_progress: Optional[dict] = None
    next_workflow: Optional[dict] = None


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: List[str] = []
    difficulty: int = 1
    deadline: Optional[datetime] = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    status: str
    technologies: List[str]
    difficulty: int
    score: Optional[int] = None
    progress: float = 0.0
    deadline: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SummaryRequest(BaseModel):
    content: str
    summary_type: str = "short_notes"
    max_length: int = 500


class SummaryResponse(BaseModel):
    title: str
    content: str
    summary_type: str
    format: str


class KeywordItem(BaseModel):
    keyword: str
    score: float
    frequency: int


class SubjectMatch(BaseModel):
    subject: str
    score: float
    matches: int


class MLAnalysisResponse(BaseModel):
    file_id: UUID
    filename: str
    file_type: str
    status: Optional[str] = None
    statistics: Optional[dict] = None
    readability: Optional[dict] = None
    difficulty: Optional[dict] = None
    keywords: List[KeywordItem] = []
    subject_matches: List[SubjectMatch] = []


class SimilarFileResponse(BaseModel):
    file_id: UUID
    title: str
    similarity: float
    file_type: Optional[str] = None
    pages: Optional[int] = None
    subject: Optional[str] = None