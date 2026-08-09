import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.core.database import get_db
from app.models.models import Subject, Unit, Chapter, Topic, Concept, File, LearningProgress
from app.schemas.schemas import (
    SubjectCreate, SubjectResponse, UnitCreate, UnitResponse,
    ChapterCreate, ChapterResponse, TopicCreate, TopicResponse,
    ConceptCreate, ConceptResponse,
)
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/subjects", tags=["Subjects"])


async def _ensure_subject_access(db: AsyncSession, subject_id: uuid.UUID, user) -> Subject:
    """Verify the subject belongs to the current user, else 404."""
    result = await db.execute(
        select(Subject).where(Subject.id == subject_id, Subject.user_id == user.id)
    )
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


async def _ensure_topic_access(db: AsyncSession, topic_id: uuid.UUID, user) -> Topic:
    """Verify the topic belongs to the current user's subject, else 404."""
    result = await db.execute(
        select(Topic)
        .join(Chapter, Topic.chapter_id == Chapter.id)
        .join(Unit, Chapter.unit_id == Unit.id)
        .join(Subject, Unit.subject_id == Subject.id)
        .where(Topic.id == topic_id, Subject.user_id == user.id)
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


# --- Subject CRUD ---
@router.post("/", response_model=SubjectResponse)
async def create_subject(
    data: SubjectCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    subject = Subject(
        user_id=user.id, **data.model_dump(exclude_none=True)
    )
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return SubjectResponse(
        id=subject.id,
        name=subject.name,
        description=subject.description,
        university=subject.university,
        semester=subject.semester,
        subject_code=subject.subject_code,
        icon=subject.icon,
        color=subject.color,
        created_at=subject.created_at,
    )


@router.get("/", response_model=List[SubjectResponse])
async def list_subjects(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(
        select(Subject).where(Subject.user_id == user.id).order_by(Subject.created_at.desc())
    )
    subjects = result.scalars().all()
    responses = []
    for s in subjects:
        unit_count = await db.scalar(select(func.count(Unit.id)).where(Unit.subject_id == s.id))
        file_count = await db.scalar(select(func.count(File.id)).where(File.subject_id == s.id))
        progress = await db.scalar(
            select(func.avg(LearningProgress.confidence)).where(
                LearningProgress.subject_id == s.id, LearningProgress.user_id == user.id
            )
        )
        responses.append(SubjectResponse(
            id=s.id, name=s.name, description=s.description, university=s.university,
            semester=s.semester, subject_code=s.subject_code, icon=s.icon, color=s.color,
            progress=float(progress or 0), unit_count=unit_count or 0, file_count=file_count or 0,
            created_at=s.created_at,
        ))
    return responses


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(subject_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(
        select(Subject).where(Subject.id == subject_id, Subject.user_id == user.id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Subject not found")
    unit_count = await db.scalar(select(func.count(Unit.id)).where(Unit.subject_id == s.id))
    file_count = await db.scalar(select(func.count(File.id)).where(File.subject_id == s.id))
    progress = await db.scalar(
        select(func.avg(LearningProgress.confidence)).where(
            LearningProgress.subject_id == s.id, LearningProgress.user_id == user.id
        )
    )
    return SubjectResponse(
        id=s.id, name=s.name, description=s.description, university=s.university,
        semester=s.semester, subject_code=s.subject_code, icon=s.icon, color=s.color,
        progress=float(progress or 0), unit_count=unit_count or 0, file_count=file_count or 0, created_at=s.created_at,
    )


@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: uuid.UUID, data: SubjectCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    result = await db.execute(select(Subject).where(Subject.id == subject_id, Subject.user_id == user.id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    for key, val in data.model_dump(exclude_none=True).items():
        setattr(subject, key, val)
    await db.commit()
    await db.refresh(subject)
    return SubjectResponse.model_validate(subject)


@router.delete("/{subject_id}")
async def delete_subject(subject_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(Subject).where(Subject.id == subject_id, Subject.user_id == user.id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    await db.delete(subject)
    await db.commit()
    return {"message": "Subject deleted"}


# --- Unit CRUD ---
@router.post("/{subject_id}/units", response_model=UnitResponse)
async def create_unit(
    subject_id: uuid.UUID, data: UnitCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    result = await db.execute(select(Subject).where(Subject.id == subject_id, Subject.user_id == user.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Subject not found")
    unit = Unit(subject_id=subject_id, **data.model_dump())
    db.add(unit)
    await db.commit()
    await db.refresh(unit)
    return UnitResponse(
        id=unit.id, subject_id=unit.subject_id, name=unit.name,
        description=unit.description, order=unit.order, created_at=unit.created_at,
    )


@router.get("/{subject_id}/units", response_model=List[UnitResponse])
async def list_units(subject_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _ensure_subject_access(db, subject_id, user)
    result = await db.execute(
        select(Unit).where(Unit.subject_id == subject_id).order_by(Unit.order)
    )
    units = result.scalars().all()
    responses = []
    for u in units:
        chapter_count = await db.scalar(select(func.count(Chapter.id)).where(Chapter.unit_id == u.id))
        responses.append(UnitResponse(
            id=u.id, subject_id=u.subject_id, name=u.name,
            description=u.description, order=u.order, chapter_count=chapter_count or 0,
            created_at=u.created_at,
        ))
    return responses


# --- Chapter CRUD ---
@router.post("/{subject_id}/units/{unit_id}/chapters", response_model=ChapterResponse)
async def create_chapter(
    subject_id: uuid.UUID, unit_id: uuid.UUID, data: ChapterCreate,
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user),
):
    await _ensure_subject_access(db, subject_id, user)
    result = await db.execute(select(Unit).where(Unit.id == unit_id, Unit.subject_id == subject_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Unit not found")
    chapter = Chapter(unit_id=unit_id, **data.model_dump())
    db.add(chapter)
    await db.commit()
    await db.refresh(chapter)
    return ChapterResponse(
        id=chapter.id, unit_id=chapter.unit_id, name=chapter.name,
        description=chapter.description, order=chapter.order,
        estimated_hours=chapter.estimated_hours, difficulty=chapter.difficulty,
        created_at=chapter.created_at,
    )


@router.get("/{subject_id}/units/{unit_id}/chapters", response_model=List[ChapterResponse])
async def list_chapters(
    subject_id: uuid.UUID, unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user),
):
    await _ensure_subject_access(db, subject_id, user)
    result = await db.execute(
        select(Chapter).where(Chapter.unit_id == unit_id).order_by(Chapter.order)
    )
    chapters = result.scalars().all()
    responses = []
    for ch in chapters:
        topic_count = await db.scalar(select(func.count(Topic.id)).where(Topic.chapter_id == ch.id))
        progress = await db.scalar(
            select(func.avg(LearningProgress.confidence)).where(
                LearningProgress.chapter_id == ch.id, LearningProgress.user_id == user.id
            )
        )
        responses.append(ChapterResponse(
            id=ch.id, unit_id=ch.unit_id, name=ch.name, description=ch.description,
            order=ch.order, estimated_hours=ch.estimated_hours, difficulty=ch.difficulty,
            topic_count=topic_count or 0, progress=float(progress or 0), created_at=ch.created_at,
        ))
    return responses


# --- Topic CRUD ---
@router.post("/{subject_id}/units/{unit_id}/chapters/{chapter_id}/topics", response_model=TopicResponse)
async def create_topic(
    subject_id: uuid.UUID, unit_id: uuid.UUID, chapter_id: uuid.UUID, data: TopicCreate,
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user),
):
    await _ensure_subject_access(db, subject_id, user)
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id, Chapter.unit_id == unit_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chapter not found")
    topic = Topic(chapter_id=chapter_id, **data.model_dump())
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return TopicResponse(
        id=topic.id, chapter_id=topic.chapter_id, name=topic.name,
        content=topic.content, summary=topic.summary, order=topic.order,
        difficulty=topic.difficulty, importance=topic.importance,
        prerequisites=topic.prerequisites or [], tags=topic.tags or [],
        created_at=topic.created_at,
    )


@router.get("/{subject_id}/units/{unit_id}/chapters/{chapter_id}/topics", response_model=List[TopicResponse])
async def list_topics(
    subject_id: uuid.UUID, unit_id: uuid.UUID, chapter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user),
):
    await _ensure_subject_access(db, subject_id, user)
    result = await db.execute(
        select(Topic).where(Topic.chapter_id == chapter_id).order_by(Topic.order)
    )
    topics = result.scalars().all()
    responses = []
    for t in topics:
        concept_count = await db.scalar(select(func.count(Concept.id)).where(Concept.topic_id == t.id))
        progress = await db.scalar(
            select(func.avg(LearningProgress.confidence)).where(
                LearningProgress.topic_id == t.id, LearningProgress.user_id == user.id
            )
        )
        responses.append(TopicResponse(
            id=t.id, chapter_id=t.chapter_id, name=t.name, content=t.content,
            summary=t.summary, order=t.order, difficulty=t.difficulty,
            importance=t.importance, prerequisites=t.prerequisites or [], tags=t.tags or [],
            concept_count=concept_count or 0, progress=float(progress or 0), created_at=t.created_at,
        ))
    return responses


# --- Concept CRUD ---
@router.post("/concepts", response_model=ConceptResponse)
async def create_concept(data: ConceptCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    concept = Concept(**data.model_dump())
    db.add(concept)
    await db.commit()
    await db.refresh(concept)
    return ConceptResponse.model_validate(concept)


@router.get("/topics/{topic_id}/concepts", response_model=List[ConceptResponse])
async def list_concepts(topic_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _ensure_topic_access(db, topic_id, user)
    result = await db.execute(
        select(Concept).where(Concept.topic_id == topic_id).order_by(Concept.difficulty)
    )
    concepts = result.scalars().all()
    return [ConceptResponse.model_validate(c) for c in concepts]