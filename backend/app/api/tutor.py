import uuid
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from app.core.database import get_db
from app.models.models import Subject, Topic, Concept, ChatHistory, Quiz, Question, QuizResponse, LearningProgress
from app.schemas.schemas import (
    ChatMessage, ChatResponse, QuizCreate, QuizResponse as QuizRespSchema,
    QuestionResponse, QuizSubmission,
)
from app.api.auth import get_current_user
from app.services.ai_service import ai_provider

router = APIRouter(prefix="/api/tutor", tags=["AI Tutor"])
logger = logging.getLogger(__name__)


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

Current learning mode: {mode}

Rules:
- NEVER give direct answers
- Always teach step by step
- Use analogies and examples
- Check understanding frequently
- Adapt to student's level
- Be encouraging and supportive
"""

    # Get topic context if specified
    context_text = ""
    if data.topic_id:
        result = await db.execute(select(Topic).where(Topic.id == data.topic_id))
        topic = result.scalar_one_or_none()
        if topic and topic.content:
            context_text = f"\nContext from {topic.name}:\n{topic.content[:2000]}"

    messages = [
        {"role": "system", "content": system_prompt.format(mode=data.mode) + context_text},
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
        result = await db.execute(select(Topic).where(Topic.id == data.topic_id))
        topic = result.scalar_one_or_none()
        if topic:
            content = topic.content or topic.summary or ""
        elif data.subject_id:
            # topic not found, but we have subject_id - don't give up yet
            data.subject_id = data.subject_id

    if not content and data.subject_id:
        # Try subject, use its name as prompt context
        result = await db.execute(select(Subject).where(Subject.id == data.subject_id))
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
    quiz = Quiz(
        user_id=user.id,
        topic_id=data.topic_id,
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
            topic_id=data.topic_id,
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
            select(Question).where(Question.id == uuid.UUID(question_id))
        )
        question = q_result.scalar_one_or_none()
        if not question:
            continue

        is_correct = user_answer.strip().lower() == str(question.correct_answer).strip().lower()
        if is_correct:
            correct += 1

        response = QuizResponse(
            quiz_id=quiz_id,
            question_id=uuid.UUID(question_id),
            user_answer=str(user_answer),
            is_correct=is_correct,
            time_taken_seconds=answer.get("time_taken", 0),
            confidence=answer.get("confidence"),
        )
        db.add(response)

    score = (correct / total * 100) if total > 0 else 0
    quiz.score = score
    quiz.completed_at = datetime.utcnow()
    quiz.passed = score >= 40

    # Update learning progress
    if quiz.topic_id:
        progress_result = await db.execute(
            select(LearningProgress).where(
                LearningProgress.user_id == user.id,
                LearningProgress.topic_id == quiz.topic_id,
            )
        )
        progress = progress_result.scalar_one_or_none()
        if progress:
            progress.score = score
            progress.confidence = min(1.0, progress.confidence + (score / 100) * 0.3)
            progress.status = "completed" if score >= 40 else "in_progress"
        else:
            db.add(LearningProgress(
                user_id=user.id,
                topic_id=quiz.topic_id,
                status="completed" if score >= 40 else "in_progress",
                score=score,
                confidence=score / 100,
            ))

    await db.commit()

    return {
        "quiz_id": str(quiz.id),
        "score": score,
        "correct": correct,
        "total": total,
        "passed": quiz.passed,
    }
