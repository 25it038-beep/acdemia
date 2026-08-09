"""Progress aggregation and persistence helpers shared by API endpoints."""
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import (
    Subject, Unit, Chapter, Topic, Quiz, QuizResponse,
    LearningProgress, StudySession, Memory,
)

PASS_THRESHOLD = 70


async def get_topic_ancestry(
    db: AsyncSession, topic_id: uuid.UUID
) -> tuple[uuid.UUID | None, uuid.UUID | None, uuid.UUID | None]:
    """Return (subject_id, unit_id, chapter_id) for a topic, tolerating gaps."""
    if not topic_id:
        return None, None, None
    topic = await db.get(Topic, topic_id)
    if not topic:
        return None, None, None
    chapter = await db.get(Chapter, topic.chapter_id) if topic.chapter_id else None
    unit = await db.get(Unit, chapter.unit_id) if chapter and chapter.unit_id else None
    return (
        unit.subject_id if unit else None,
        unit.id if unit else None,
        chapter.id if chapter else None,
    )


def _merge_tags(progress: LearningProgress, strengths: list, weaknesses: list):
    existing_strengths = set(progress.strengths or [])
    existing_strengths.update(strengths or [])
    progress.strengths = sorted(existing_strengths)[:20]

    existing_weaknesses = set(progress.weaknesses or [])
    existing_weaknesses.update(weaknesses or [])
    progress.weaknesses = sorted(existing_weaknesses)[:20]


async def upsert_topic_progress(
    db: AsyncSession,
    user_id: uuid.UUID,
    topic_id: uuid.UUID,
    subject_id: uuid.UUID | None,
    unit_id: uuid.UUID | None,
    chapter_id: uuid.UUID | None,
    score: float,
    time_seconds: int,
    strengths: list | None = None,
    weaknesses: list | None = None,
) -> LearningProgress:
    """Create or update the LearningProgress row for a topic after a quiz."""
    result = await db.execute(
        select(LearningProgress).where(
            LearningProgress.user_id == user_id,
            LearningProgress.topic_id == topic_id,
        )
    )
    progress = result.scalar_one_or_none()
    now = datetime.utcnow()
    completed = score >= PASS_THRESHOLD

    if progress:
        progress.attempts += 1
        progress.score = score
        progress.confidence = max(progress.confidence or 0.0, score / 100)
        progress.status = (
            "completed" if (completed or progress.status == "completed") else "in_progress"
        )
        progress.time_spent_minutes += int(time_seconds / 60)
        if progress.status == "completed" and not progress.completed_at:
            progress.completed_at = now
        progress.subject_id = subject_id or progress.subject_id
        progress.unit_id = unit_id or progress.unit_id
        progress.chapter_id = chapter_id or progress.chapter_id
        _merge_tags(progress, strengths, weaknesses)
    else:
        progress = LearningProgress(
            user_id=user_id,
            topic_id=topic_id,
            subject_id=subject_id,
            unit_id=unit_id,
            chapter_id=chapter_id,
            status="completed" if completed else "in_progress",
            confidence=score / 100,
            score=score,
            attempts=1,
            time_spent_minutes=int(time_seconds / 60),
            strengths=strengths or [],
            weaknesses=weaknesses or [],
            completed_at=now if completed else None,
        )
        db.add(progress)
    return progress


async def get_progress_summary(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Aggregate the user's full progress state. Pure read, always fresh."""
    subjects = (
        (await db.execute(select(Subject).where(Subject.user_id == user_id))).scalars().all()
    )
    units = (await db.execute(select(Unit))).scalars().all()
    chapters = (await db.execute(select(Chapter))).scalars().all()
    topics = (await db.execute(select(Topic))).scalars().all()

    unit_by_id = {u.id: u for u in units}
    chapter_by_id = {c.id: c for c in chapters}

    def topic_subject_id(t: Topic):
        chapter = chapter_by_id.get(t.chapter_id)
        if not chapter:
            return None
        unit = unit_by_id.get(chapter.unit_id)
        return unit.subject_id if unit else None

    topics_by_subject = defaultdict(list)
    for t in topics:
        sid = topic_subject_id(t)
        if sid is not None:
            topics_by_subject[sid].append(t)

    progress_rows = (
        (await db.execute(
            select(LearningProgress).where(LearningProgress.user_id == user_id)
        )).scalars().all()
    )
    progress_by_topic = {}
    for p in progress_rows:
        progress_by_topic[p.topic_id] = p

    total_topics = sum(len(v) for v in topics_by_subject.values())
    mastered = 0
    for t in topics:
        p = progress_by_topic.get(t.id)
        if p and p.status == "completed":
            mastered += 1
    completion = (mastered / total_topics * 100) if total_topics else 0.0

    topic_rows = [p for p in progress_rows if p.topic_id is not None]
    confidences = [p.confidence or 0.0 for p in topic_rows]
    mastery = (sum(confidences) / len(confidences) * 100) if confidences else 0.0

    per_subject = []
    for s in subjects:
        s_topics = topics_by_subject.get(s.id, [])
        s_conf = [
            p.confidence or 0.0
            for p in topic_rows
            if p.subject_id == s.id and p.topic_id is not None
        ]
        s_mastered = sum(
            1 for t in s_topics
            if progress_by_topic.get(t.id) and progress_by_topic[t.id].status == "completed"
        )
        per_subject.append({
            "id": str(s.id),
            "name": s.name,
            "icon": s.icon,
            "color": s.color,
            "progress": round((sum(s_conf) / len(s_conf) * 100) if s_conf else 0.0, 1),
            "topics_learned": s_mastered,
            "topics_total": len(s_topics),
        })

    quizzes = (
        (await db.execute(
            select(Quiz).where(Quiz.user_id == user_id, Quiz.completed_at.isnot(None))
        )).scalars().all()
    )
    scores = [q.score or 0 for q in quizzes]
    quiz_ids = [q.id for q in quizzes]
    time_by_quiz = defaultdict(int)
    if quiz_ids:
        responses = (
            (await db.execute(
                select(QuizResponse).where(QuizResponse.quiz_id.in_(quiz_ids))
            )).scalars().all()
        )
        for r in responses:
            time_by_quiz[r.quiz_id] += r.time_taken_seconds or 0

    trend = []
    for q in sorted(quizzes, key=lambda x: x.completed_at or datetime.min, reverse=True)[:10]:
        trend.append({
            "date": (q.completed_at or datetime.utcnow()).strftime("%m/%d"),
            "score": round(q.score or 0, 1),
            "title": q.title,
        })
    trend.reverse()

    sessions = (
        (await db.execute(
            select(StudySession).where(StudySession.user_id == user_id)
        )).scalars().all()
    )
    total_minutes = sum(s.duration_minutes or 0 for s in sessions)
    total_minutes += sum(time_by_quiz.values()) // 60
    total_hours = round(total_minutes / 60, 1)

    today = datetime.utcnow().date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    weekly = []
    for d in days:
        minutes = sum(
            (s.duration_minutes or 0)
            for s in sessions
            if s.started_at and s.started_at.date() == d
        )
        minutes += sum(
            time_by_quiz.get(q.id, 0) // 60
            for q in quizzes
            if q.completed_at and q.completed_at.date() == d
        )
        weekly.append({
            "day": d.strftime("%a"),
            "date": d.isoformat(),
            "hours": round(minutes / 60, 2),
        })

    activity = set()
    for s in sessions:
        if s.started_at:
            activity.add(s.started_at.date())
    for q in quizzes:
        if q.completed_at:
            activity.add(q.completed_at.date())
    memories = (
        (await db.execute(
            select(Memory).where(Memory.user_id == user_id, Memory.last_recalled.isnot(None))
        )).scalars().all()
    )
    for m in memories:
        if m.last_recalled:
            activity.add(m.last_recalled.date())

    streak = 0
    cursor = today if today in activity else today - timedelta(days=1)
    while cursor in activity:
        streak += 1
        cursor -= timedelta(days=1)

    return {
        "overall": {
            "mastery": round(mastery, 1),
            "completion": round(completion, 1),
            "topics_learned": mastered,
            "topics_total": total_topics,
        },
        "hours": {"total_hours": total_hours, "weekly": weekly},
        "quizzes": {
            "count": len(quizzes),
            "passed": sum(1 for q in quizzes if q.passed),
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
            "trend": trend,
        },
        "streak": streak,
        "subjects": per_subject,
    }
