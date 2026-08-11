import uuid
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional
from app.core.database import get_db
from app.models.models import Subject, Topic, Concept, ChatHistory, Quiz, Question, QuizResponse, LearningProgress, File, Chunk, Chapter, Unit, Notification, to_uuid
from app.schemas.schemas import (
    ChatMessage, ChatResponse, QuizCreate, QuizResponse as QuizRespSchema,
    QuestionResponse, QuizSubmission, ChatMessageOut, ChatSessionSummary,
)
from app.api.auth import get_current_user
from app.api.notifications import create_notification
from app.services.ai_service import ai_provider
from app.services.progress_service import (
    PASS_THRESHOLD, get_topic_ancestry, upsert_topic_progress,
)

router = APIRouter(prefix="/api/tutor", tags=["AI Tutor"])
logger = logging.getLogger(__name__)


async def _build_context(
    db: AsyncSession,
    user,
    message: str,
    subject_id: Optional[uuid.UUID],
    topic_id: Optional[uuid.UUID],
) -> tuple[str, Optional[Subject]]:
    """Gather course material context from uploaded files/chunks relevant to the question."""
    subject = None
    context_parts = []

    if subject_id:
        result = await db.execute(select(Subject).where(Subject.id == subject_id, Subject.user_id == user.id))
        subject = result.scalar_one_or_none()
        if subject:
            context_parts.append(
                f"Course: {subject.name}\n{subject.description or ''}".strip()
            )

    # Collect chunks from the user's files (scoped to selected subject, or all files)
    file_stmt = select(File).where(File.user_id == user.id)
    if subject_id:
        file_stmt = file_stmt.where(File.subject_id == subject_id)
    file_stmt = file_stmt.where(File.status == "completed").order_by(File.created_at.desc()).limit(10)
    files = (await db.execute(file_stmt)).scalars().all()

    if files:
        chunk_stmt = (
            select(Chunk)
            .where(Chunk.file_id.in_([f.id for f in files]))
            .order_by(Chunk.chunk_index)
        )
        chunks = (await db.execute(chunk_stmt)).scalars().all()
    else:
        chunks = []

    if chunks:
        # Simple relevance scoring (keyword overlap) since vector store may be unavailable
        query_terms = set(_tokenize(message))

        def score(chunk: Chunk) -> float:
            text = (chunk.content or "").lower()
            return sum(1 for t in query_terms if t in text)

        scored = sorted(chunks, key=score, reverse=True)
        # Include all chunks when few, otherwise the top relevant ones
        top = scored[:12] if len(scored) > 12 else scored
        for c in top:
            snippet = (c.content or "").strip()
            if snippet:
                context_parts.append(snippet)

    if context_parts:
        joined = "\n\n".join(context_parts)
        return f"=== COURSE MATERIAL (use this to answer) ===\n{joined[:12000]}", subject
    return "", subject


def _tokenize(text: str) -> list[str]:
    import re
    return [t for t in re.split(r"[^a-zA-Z0-9]+", text.lower()) if len(t) > 2]


async def _build_chat_reference(
    db: AsyncSession,
    user,
    message: str,
    current_session_id: str,
    limit: int = 6,
) -> str:
    """Pull relevant past AI conversations across the learner's sessions as reference context."""
    query_terms = set(_tokenize(message))
    if not query_terms:
        return ""

    stmt = (
        select(ChatHistory)
        .where(
            ChatHistory.user_id == user.id,
            ChatHistory.role == "assistant",
            ChatHistory.session_id != current_session_id,
        )
        .order_by(desc(ChatHistory.created_at))
        .limit(200)
    )
    rows = (await db.execute(stmt)).scalars().all()

    scored = []
    for row in rows:
        text = (row.content or "").lower()
        score = sum(1 for t in query_terms if t in text)
        if score > 0:
            scored.append((score, row))
    scored.sort(key=lambda x: -x[0])
    top = scored[:limit]

    parts = []
    for _, row in top:
        snippet = (row.content or "").strip()
        if snippet:
            parts.append(f"--- Past AI tutoring response (session {row.session_id}) ---\n{snippet[:800]}")
    if not parts:
        return ""
    return (
        "=== PREVIOUS CONVERSATIONS (use only as reference if directly relevant; "
        "never contradict the current question, and keep the answer fresh) ===\n"
        + "\n\n".join(parts)
    )


@router.get("/sessions", response_model=List[ChatSessionSummary])
async def list_chat_sessions(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """List all past chat conversations for the user."""
    stmt = (
        select(
            ChatHistory.session_id,
            func.max(ChatHistory.created_at).label("last_updated"),
            func.count(ChatHistory.id).label("message_count"),
        )
        .where(ChatHistory.user_id == user.id)
        .group_by(ChatHistory.session_id)
        .order_by(func.max(ChatHistory.created_at).desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    sessions = []
    for session_id, last_updated, message_count in rows:
        first_result = await db.execute(
            select(ChatHistory.content)
            .where(
                ChatHistory.session_id == session_id,
                ChatHistory.user_id == user.id,
                ChatHistory.role == "user",
            )
            .order_by(ChatHistory.created_at.asc())
            .limit(1)
        )
        first_message = first_result.scalar_one_or_none() or ""
        sessions.append(
            ChatSessionSummary(
                session_id=session_id,
                first_message=first_message,
                message_count=message_count,
                last_updated=last_updated,
            )
        )
    return sessions


@router.get("/history", response_model=List[ChatMessageOut])
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Fetch the full message history of a chat session."""
    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.session_id == session_id, ChatHistory.user_id == user.id)
        .order_by(ChatHistory.created_at.asc())
    )
    return result.scalars().all()


@router.post("/chat", response_model=ChatResponse)
async def chat_with_tutor(
    data: ChatMessage,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # Build context from knowledge base
    system_prompt = """You are an expert AI Professor at Academia AI. You NEVER give direct answers.
    
Teaching methodology:
1. First, EXPLAIN the concept simply
2. Then SIMPLIFY with an easy analogy
3. Ask a question to check understanding
4. Evaluate the student's response
5. Correct mistakes gently
6. Only then continue to next concept

Current learning mode (theme): {mode}

=== LEARNER PROFILE (use this in every response) ===
{profile}

Personalization rules:
- ALWAYS address the learner by their first name (from the Name field, e.g., "Welcome, Alex", "Great question, Alex!", "Since you're studying Data Structures, Alex..."). Use the name naturally throughout the response.
- Know the learner's enrolled courses (listed under "Enrolled Courses") and REFERENCE them in responses: when a question relates to one of their courses, explicitly mention that course by name and connect the teaching to it.
- Use course references to make answers personal, e.g., "In your Data Structures course, you'll use this when...", "This connects directly to your Machine Learning subject."
- If no enrolled courses exist, do not invent any; teach generically instead.
- Match the depth, terminology, and examples to their education level
- Frame analogies and examples inside their domain
- Align teaching style with the learning theme
- If any profile field is empty, fall back to neutral "learner" wording

Rules:
- NEVER give direct answers
- Always teach step by step
- Use analogies and examples
- Check understanding frequently
- Adapt to student's level
- Be encouraging and supportive
"""

    # Enrolled courses (subjects) for this learner
    enrolled_result = await db.execute(
        select(Subject).where(Subject.user_id == user.id).order_by(Subject.name)
    )
    enrolled_courses = enrolled_result.scalars().all()

    profile_parts = []
    learner_name = user.full_name or user.username
    if learner_name:
        profile_parts.append(f"Name: {learner_name}")
    if user.occupation:
        profile_parts.append(f"Designation (what they do): {user.occupation}")
    if user.education_level:
        profile_parts.append(f"Education level: {user.education_level}")
    if user.domain:
        profile_parts.append(f"Domain: {user.domain}")
    if user.course:
        profile_parts.append(f"Course/Program: {user.course}")
    if user.university:
        profile_parts.append(f"University/Institution: {user.university}")
    if enrolled_courses:
        course_names = [s.name for s in enrolled_courses]
        profile_parts.append(f"Enrolled Courses: {', '.join(course_names)}")
    profile_text = "\n".join(profile_parts) if profile_parts else "Not provided - treat the learner generically."

    # Get topic context if specified (scoped to the user's own subjects)
    context_text = ""
    if data.topic_id:
        topic_id = to_uuid(data.topic_id)
        result = await db.execute(
            select(Topic)
            .join(Chapter, Topic.chapter_id == Chapter.id)
            .join(Unit, Chapter.unit_id == Unit.id)
            .join(Subject, Unit.subject_id == Subject.id)
            .where(Topic.id == topic_id, Subject.user_id == user.id)
        )
        topic = result.scalar_one_or_none()
        if topic and topic.content:
            context_text = f"\nContext from {topic.name}:\n{topic.content[:2000]}"

    # Get course material context from uploaded files
    course_context, subject = await _build_context(db, user, data.message, data.subject_id, data.topic_id)
    if course_context:
        context_text += f"\n\n{course_context}"
        context_text += (
            "\n\nIMPORTANT INSTRUCTIONS FOR COURSE MATERIAL:"
            "\n- The 'COURSE MATERIAL' section above comes from the student's uploaded files."
            "\n- When the question relates to course content, teach FROM this material."
            "\n- Reference specific facts, definitions, examples, or figures from the material."
            "\n- If the material does not cover the question, say so briefly, then teach with general knowledge."
            "\n- Never invent facts that contradict the provided course material."
        )

    # Pull relevant past conversations as reference
    chat_reference = await _build_chat_reference(db, user, data.message, data.session_id)
    if chat_reference:
        context_text += f"\n\n{chat_reference}"

    messages = [
        {"role": "system", "content": system_prompt.format(mode=data.mode, profile=profile_text) + context_text},
    ]

    # Add recent chat history (last 10 messages)
    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.session_id == data.session_id, ChatHistory.user_id == user.id)
        .order_by(desc(ChatHistory.created_at))
        .limit(10)
    )
    history = reversed(result.scalars().all())
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    # Add user message
    messages.append({"role": "user", "content": data.message})

    # Save user message
    db.add(ChatHistory(
        user_id=user.id, session_id=data.session_id, role="user", content=data.message
    ))

    # Get AI response
    response_content = ""
    async for chunk in ai_provider.chat(messages, temperature=0.7, stream=False):
        chunk_data = json.loads(chunk)
        response_content += chunk_data.get("content", "")

    # Save AI response
    db.add(ChatHistory(
        user_id=user.id, session_id=data.session_id, role="assistant", content=response_content
    ))
    await db.commit()

    return ChatResponse(session_id=data.session_id, message=response_content)


@router.post("/quiz/generate", response_model=dict)
async def generate_quiz(
    data: QuizCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    content = ""

    if data.topic_id:
        topic_id = to_uuid(data.topic_id)
        result = await db.execute(
            select(Topic)
            .join(Chapter, Topic.chapter_id == Chapter.id)
            .join(Unit, Chapter.unit_id == Unit.id)
            .join(Subject, Unit.subject_id == Subject.id)
            .where(Topic.id == topic_id, Subject.user_id == user.id)
        )
        topic = result.scalar_one_or_none()
        if topic:
            content = topic.content or topic.summary or ""
        elif data.subject_id:
            # topic not found, but we have subject_id - don't give up yet
            data.subject_id = data.subject_id

    if not content and data.subject_id:
        # Try subject, use its name as prompt context (scoped to the user's own subject)
        result = await db.execute(
            select(Subject).where(Subject.id == data.subject_id, Subject.user_id == user.id)
        )
        subject = result.scalar_one_or_none()
        if subject:
            content = f"Generate a quiz about: {subject.name}. {subject.description or ''}"
        else:
            content = f"Generate a quiz about: {data.title}"

    if not content:
        content = f"Generate a quiz about: {data.title}"
    questions = await ai_provider.generate_questions(
        content=content[:5000],
        question_type=data.quiz_type,
        count=data.question_count,
        difficulty=data.difficulty,
    )

    # Create quiz
    topic_id = to_uuid(data.topic_id)
    quiz = Quiz(
        user_id=user.id,
        subject_id=to_uuid(data.subject_id),
        topic_id=topic_id,
        title=data.title,
        quiz_type=data.quiz_type,
        difficulty=data.difficulty,
        time_limit_minutes=data.time_limit_minutes,
        total_questions=len(questions),
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)

    # Create question records
    for q in questions:
        question = Question(
            quiz_id=quiz.id,
            topic_id=topic_id,
            question_text=q.get("question_text", ""),
            question_type=q.get("question_type", data.quiz_type),
            options=q.get("options"),
            correct_answer=str(q.get("correct_answer", "")),
            explanation=q.get("explanation", ""),
            difficulty=q.get("difficulty", 1),
            marks=q.get("marks", 1),
        )
        db.add(question)

    await db.commit()

    return {
        "quiz_id": str(quiz.id),
        "title": quiz.title,
        "total_questions": len(questions),
        "time_limit_minutes": quiz.time_limit_minutes,
    }


@router.get("/quiz/{quiz_id}", response_model=dict)
async def get_quiz(
    quiz_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == user.id)
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions_result = await db.execute(
        select(Question).where(Question.quiz_id == quiz_id)
    )
    questions = questions_result.scalars().all()

    return {
        "id": str(quiz.id),
        "title": quiz.title,
        "quiz_type": quiz.quiz_type,
        "difficulty": quiz.difficulty,
        "time_limit_minutes": quiz.time_limit_minutes,
        "total_questions": quiz.total_questions,
        "completed": quiz.completed_at is not None,
        "score": quiz.score,
        "questions": [
            {
                "id": str(q.id),
                "question_text": q.question_text,
                "question_type": q.question_type,
                "options": q.options,
                "difficulty": q.difficulty,
                "marks": q.marks,
            }
            for q in questions
        ],
    }


@router.post("/quiz/{quiz_id}/submit", response_model=dict)
async def submit_quiz(
    quiz_id: uuid.UUID,
    data: QuizSubmission,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == user.id)
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    correct = 0
    total = len(data.answers)

    for answer in data.answers:
        question_id = answer.get("question_id")
        user_answer = answer.get("answer", "")

        q_result = await db.execute(
            select(Question).where(Question.id == to_uuid(question_id), Question.quiz_id == quiz_id)
        )
        question = q_result.scalar_one_or_none()
        if not question:
            continue

        is_correct = user_answer.strip().lower() == str(question.correct_answer).strip().lower()
        if is_correct:
            correct += 1

        response = QuizResponse(
            quiz_id=quiz_id,
            question_id=to_uuid(question_id),
            user_answer=str(user_answer),
            is_correct=is_correct,
            time_taken_seconds=answer.get("time_taken", 0),
            confidence=answer.get("confidence"),
        )
        db.add(response)

    score = (correct / total * 100) if total > 0 else 0
    quiz.score = score
    quiz.completed_at = datetime.utcnow()
    quiz.passed = score >= PASS_THRESHOLD

    # Resolve the topic this quiz belongs to: quiz topic → first question topic → first topic of the subject
    questions_result = await db.execute(
        select(Question).where(Question.quiz_id == quiz_id)
    )
    questions = questions_result.scalars().all()
    topic_id = quiz.topic_id or next((q.topic_id for q in questions if q.topic_id), None)
    if not topic_id and quiz.subject_id:
        topic = await db.scalar(
            select(Topic)
            .join(Chapter, Topic.chapter_id == Chapter.id)
            .join(Unit, Chapter.unit_id == Unit.id)
            .where(Unit.subject_id == quiz.subject_id)
            .order_by(Topic.created_at)
            .limit(1)
        )
        if topic:
            topic_id = topic.id
            quiz.topic_id = topic_id

    # Track time + strengths/weaknesses from this attempt
    total_time_seconds = sum(int(a.get("time_taken", 0) or 0) for a in data.answers)
    strengths = []
    weaknesses = []
    for answer in data.answers:
        q_result = await db.execute(
            select(Question).where(Question.id == to_uuid(answer.get("question_id", "")))
        )
        question = q_result.scalar_one_or_none()
        if not question:
            continue
        tags = [str(t) for t in (question.tags or [])][:5]
        is_correct = (str(answer.get("answer", "")).strip().lower()
                      == str(question.correct_answer or "").strip().lower())
        if tags:
            if is_correct:
                strengths.extend(tags)
            else:
                weaknesses.extend(tags)

    # Update learning progress for the resolved topic
    if topic_id:
        subject_id, unit_id, chapter_id = await get_topic_ancestry(db, topic_id)
        await upsert_topic_progress(
            db, user.id, topic_id, subject_id, unit_id, chapter_id,
            score, total_time_seconds, strengths, weaknesses,
        )

    await db.commit()

    # ── Notifications ────────────────────────────────────────────────────────
    # Quiz completed successfully → notify user
    passed_label = "passed" if quiz.passed else "needs review"
    await create_notification(
        db,
        user.id,
        "Quiz Completed Successfully",
        f"You scored {score:.0f}% on \"{quiz.title}\" ({passed_label}). Progress has been updated.",
        notification_type="quiz",
        action_url="/progress",
    )

    # Chapter/course completed → notify user once all its topics are mastered
    if topic_id:
        topic_result = await db.execute(
            select(Topic)
            .join(Chapter, Topic.chapter_id == Chapter.id)
            .join(Unit, Chapter.unit_id == Unit.id)
            .join(Subject, Unit.subject_id == Subject.id)
            .where(Topic.id == topic_id, Subject.user_id == user.id)
        )
        topic = topic_result.scalar_one_or_none()
        if topic and topic.chapter_id:
            chapter = await db.get(Chapter, topic.chapter_id)
            if chapter:
                topics_result = await db.execute(
                    select(Topic).where(Topic.chapter_id == chapter.id)
                )
                chapter_topics = topics_result.scalars().all()
                if chapter_topics:
                    progress_result = await db.execute(
                        select(LearningProgress).where(
                            LearningProgress.user_id == user.id,
                            LearningProgress.topic_id.in_([t.id for t in chapter_topics]),
                        )
                    )
                    progresses = progress_result.scalars().all()
                    completed_topic_ids = {
                        p.topic_id for p in progresses if p.status == "completed"
                    }
                    chapter_done = all(t.id in completed_topic_ids for t in chapter_topics)

                    if chapter_done:
                        existing = await db.execute(
                            select(Notification).where(
                                Notification.user_id == user.id,
                                Notification.title == f"Chapter Completed: {chapter.name}",
                            )
                        )
                        if not existing.scalar_one_or_none():
                            await create_notification(
                                db,
                                user.id,
                                f"Chapter Completed: {chapter.name}",
                                "Congratulations! You have mastered every topic in this chapter. Progress stored successfully.",
                                notification_type="course",
                                action_url="/progress",
                            )

    await db.commit()

    return {
        "quiz_id": str(quiz.id),
        "score": score,
        "correct": correct,
        "total": total,
        "passed": quiz.passed,
    }
