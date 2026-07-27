import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Enum as SAEnum, Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return uuid.uuid4()


class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    UNIVERSITY = "university"


class LearningMode(str, enum.Enum):
    BEGINNER = "beginner"
    SCHOOL = "school"
    COLLEGE = "college"
    ENGINEERING = "engineering"
    RESEARCH = "research"
    INTERVIEW = "interview"
    EXAM = "exam"
    CODING = "coding"
    VISUAL = "visual"
    STORY = "story"
    REVISION = "revision"


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.STUDENT)
    avatar_url = Column(String(500), nullable=True)
    university = Column(String(255), nullable=True)
    course = Column(String(255), nullable=True)
    semester = Column(Integer, nullable=True)
    learning_mode = Column(SAEnum(LearningMode), default=LearningMode.COLLEGE)
    preferences = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    subjects = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    files = relationship("File", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("LearningProgress", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    user_id = Column(Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    university = Column(String(255), nullable=True)
    semester = Column(Integer, nullable=True)
    subject_code = Column(String(50), nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)
    syllabus = Column(JSON, default=dict)
    extra_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="subjects")
    units = relationship("Unit", back_populates="subject", cascade="all, delete-orphan")
    files = relationship("File", back_populates="subject")
    progress = relationship("LearningProgress", back_populates="subject")


class Unit(Base):
    __tablename__ = "units"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    subject_id = Column(Uuid(), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    subject = relationship("Subject", back_populates="units")
    chapters = relationship("Chapter", back_populates="unit", cascade="all, delete-orphan")
    progress = relationship("LearningProgress", back_populates="unit")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    unit_id = Column(Uuid(), ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=0)
    estimated_hours = Column(Float, default=1.0)
    difficulty = Column(Integer, default=1)
    created_at = Column(DateTime, default=utcnow)

    unit = relationship("Unit", back_populates="chapters")
    topics = relationship("Topic", back_populates="chapter", cascade="all, delete-orphan")
    progress = relationship("LearningProgress", back_populates="chapter")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    chapter_id = Column(Uuid(), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    order = Column(Integer, default=0)
    difficulty = Column(Integer, default=1)
    importance = Column(Integer, default=5)
    prerequisites = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)

    chapter = relationship("Chapter", back_populates="topics")
    concepts = relationship("Concept", back_populates="topic", cascade="all, delete-orphan")
    progress = relationship("LearningProgress", back_populates="topic")
    questions = relationship("Question", back_populates="topic", cascade="all, delete-orphan")


class Concept(Base):
    __tablename__ = "concepts"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    topic_id = Column(Uuid(), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=True)
    definition = Column(Text, nullable=True)
    formula = Column(Text, nullable=True)
    code_example = Column(Text, nullable=True)
    analogy = Column(Text, nullable=True)
    examples = Column(JSON, default=list)
    difficulty = Column(Integer, default=1)
    importance = Column(Integer, default=5)
    parent_concept_id = Column(Uuid(), ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True)
    exam_frequency = Column(Integer, default=0)
    extra_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)

    topic = relationship("Topic", back_populates="concepts")
    parent_concept = relationship("Concept", remote_side=[id], back_populates="child_concepts")
    child_concepts = relationship("Concept", back_populates="parent_concept", cascade="all, delete-orphan")
    knowledge_relations = relationship("KnowledgeRelation", foreign_keys="KnowledgeRelation.source_concept_id", cascade="all, delete-orphan")


class KnowledgeRelation(Base):
    __tablename__ = "knowledge_relations"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    source_concept_id = Column(Uuid(), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    target_concept_id = Column(Uuid(), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String(50), default="related_to")  # prerequisite, related, extends, etc.
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=utcnow)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    user_id = Column(Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, archived
    technologies = Column(JSON, default=list)
    difficulty = Column(Integer, default=1)
    github_url = Column(String(500), nullable=True)
    demo_url = Column(String(500), nullable=True)
    score = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="projects")
    files = relationship("File", back_populates="project")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    project_id = Column(Uuid(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    priority = Column(String(20), default="medium")
    order = Column(Integer, default=0)
    assigned_to = Column(Uuid(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="tasks")


class File(Base):
    __tablename__ = "files"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    user_id = Column(Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Uuid(), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(Uuid(), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), nullable=True)
    minio_path = Column(String(500), nullable=True)
    status = Column(String(50), default="uploaded")
    pages = Column(Integer, default=0)
    chunks = Column(Integer, default=0)
    extracted_text = Column(Text, nullable=True)
    extra_metadata = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="files")
    subject = relationship("Subject", back_populates="files")
    project = relationship("Project", back_populates="files")
    chunks_rel = relationship("Chunk", back_populates="file", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    file_id = Column(Uuid(), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, default=0)
    chunk_type = Column(String(50), default="text")
    embedding_id = Column(String(500), nullable=True)
    extra_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)

    file = relationship("File", back_populates="chunks_rel")


class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    user_id = Column(Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Uuid(), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    unit_id = Column(Uuid(), ForeignKey("units.id", ondelete="SET NULL"), nullable=True)
    chapter_id = Column(Uuid(), ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True)
    topic_id = Column(Uuid(), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="not_started")
    confidence = Column(Float, default=0.0)
    score = Column(Float, nullable=True)
    time_spent_minutes = Column(Integer, default=0)
    attempts = Column(Integer, default=0)
    strengths = Column(JSON, default=list)
    weaknesses = Column(JSON, default=list)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="progress")
    subject = relationship("Subject", back_populates="progress")
    unit = relationship("Unit", back_populates="progress")
    chapter = relationship("Chapter", back_populates="progress")
    topic = relationship("Topic", back_populates="progress")


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    user_id = Column(Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Uuid(), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    session_type = Column(String(50), default="study")
    duration_minutes = Column(Integer, default=0)
    focus_score = Column(Float, nullable=True)
    topics_covered = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="sessions")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    user_id = Column(Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(Uuid(), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    quiz_type = Column(String(50), default="mcq")
    difficulty = Column(String(20), default="medium")
    time_limit_minutes = Column(Integer, nullable=True)
    total_questions = Column(Integer, default=0)
    score = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    responses = relationship("QuizResponse", back_populates="quiz", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    quiz_id = Column(Uuid(), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=True)
    topic_id = Column(Uuid(), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="mcq")
    options = Column(JSON, nullable=True)
    correct_answer = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    difficulty = Column(Integer, default=1)
    marks = Column(Integer, default=1)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)

    quiz = relationship("Quiz", back_populates="questions")
    topic = relationship("Topic", back_populates="questions")


class QuizResponse(Base):
    __tablename__ = "quiz_responses"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    quiz_id = Column(Uuid(), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Uuid(), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    user_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    time_taken_seconds = Column(Integer, default=0)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    quiz = relationship("Quiz", back_populates="responses")


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    user_id = Column(Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    memory_type = Column(String(50), default="fact")
    content = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    importance = Column(Integer, default=1)
    recall_count = Column(Integer, default=0)
    last_recalled = Column(DateTime, nullable=True)
    forgetting_curve = Column(Float, default=1.0)
    extra_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="memories")


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    user_id = Column(Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(Uuid(), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    easiness = Column(Float, default=2.5)
    interval = Column(Integer, default=0)
    repetitions = Column(Integer, default=0)
    next_review = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    user_id = Column(Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    exam_date = Column(DateTime, nullable=True)
    daily_hours = Column(Float, default=2.0)
    plan_data = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    user_id = Column(Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(100), index=True, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    extra_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)


class Whiteboard(Base):
    __tablename__ = "whiteboards"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    user_id = Column(Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), default="Untitled")
    elements = Column(JSON, default=list)
    is_collaborative = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Uuid(), primary_key=True, default=new_uuid)
    user_id = Column(Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="info")
    is_read = Column(Boolean, default=False)
    action_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utcnow)