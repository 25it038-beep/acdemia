import uuid
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List
from app.core.database import get_db
from app.models.models import (
    KnowledgeRelation, Concept, Topic, LearningProgress,
    StudySession, StudyPlan, Memory, Flashcard, Whiteboard,
    Unit, Chapter, Subject, Quiz, Question, to_uuid,
)
from app.schemas.schemas import (
    KnowledgeGraphResponse, WorkflowResponse, MemoryResponse,
    StudyPlanRequest, WhiteboardCreate, WhiteboardUpdate,
    FlashcardCreate, FlashcardGenerate, StudySessionStart,
)
from app.api.auth import get_current_user

router = APIRouter(prefix="/api", tags=["Learning"])
logger = logging.getLogger(__name__)


# --- Knowledge Graph ---
@router.get("/knowledge-graph", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(
    subject_id: str = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    from app.services.knowledge_service import knowledge_graph as kg
    return await kg.get_concept_graph(str(user.id), subject_id)


@router.get("/learning-path/{concept_id}")
async def get_learning_path(
    concept_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    from app.services.knowledge_service import knowledge_graph as kg
    return await kg.get_learning_path(str(user.id), concept_id)


# --- Workflow Maps ---
@router.get("/workflow/{subject_id}", response_model=WorkflowResponse)
async def get_workflow(
    subject_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    from app.services.ai_service import ai_provider

    # Verify the subject belongs to the current user
    subject_result = await db.execute(
        select(Subject).where(Subject.id == subject_id, Subject.user_id == user.id)
    )
    if not subject_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Subject not found")

    # Get all units, chapters, topics for this subject
    result = await db.execute(
        select(Unit).where(Unit.subject_id == subject_id).order_by(Unit.order)
    )
    units = result.scalars().all()

    nodes = []
    edges = []
    total_chapters = 0
    completed_chapters = 0
    total_units = len(units)
    completed_units = 0
    next_workflow = None

    for ui, unit in enumerate(units):
        unit_node_id = f"unit_{unit.id}"
        unit_status = "pending"

        chapters_result = await db.execute(
            select(Chapter).where(Chapter.unit_id == unit.id).order_by(Chapter.order)
        )
        chapters = chapters_result.scalars().all()
        total_chapters += len(chapters)

        unit_completed = 0
        for i, chapter in enumerate(chapters):
            chapter_node_id = f"chapter_{chapter.id}"
            progress = await db.scalar(
                select(func.avg(LearningProgress.confidence)).where(
                    LearningProgress.chapter_id == chapter.id,
                    LearningProgress.user_id == user.id,
                )
            )
            status = "pending"
            if not progress or progress == 0:
                status = "pending"
            elif progress < 0.5:
                status = "weak"
            elif progress < 0.8:
                status = "in_progress"
            else:
                status = "completed"
                unit_completed += 1
                completed_chapters += 1

            nodes.append({
                "id": chapter_node_id,
                "type": "chapter",
                "label": chapter.name,
                "data": {
                    "id": str(chapter.id),
                    "type": "chapter",
                    "status": status,
                    "confidence": float(progress or 0),
                    "estimated_hours": chapter.estimated_hours,
                    "difficulty": chapter.difficulty,
                },
            })
            edges.append({
                "source": unit_node_id,
                "target": chapter_node_id,
                "label": f"{chapter.estimated_hours}h",
            })

            # if first chapter, connect to unit directly
            if i == 0:
                edges.append({
                    "source": unit_node_id,
                    "target": chapter_node_id,
                })

            # Connect chapters sequentially
            if i > 0:
                prev_id = f"chapter_{chapters[i-1].id}"
                edges.append({
                    "source": prev_id,
                    "target": chapter_node_id,
                    "label": "next",
                })

        if len(chapters) == 0:
            unit_status = "pending"
        elif unit_completed >= len(chapters):
            unit_status = "completed"
            completed_units += 1
        elif ui > 0 and units[ui - 1].id and not _unit_is_completed(db, units[ui - 1], user.id):
            unit_status = "locked"
        else:
            unit_status = "in_progress"

        if unit_status != "completed" and not next_workflow:
            next_workflow = {
                "unit_id": str(unit.id),
                "unit_name": unit.name,
                "unit_status": unit_status,
            }

        nodes.append({
            "id": unit_node_id,
            "type": "unit",
            "label": unit.name,
            "data": {
                "id": str(unit.id),
                "type": "unit",
                "status": unit_status,
                "completed_chapters": unit_completed,
                "total_chapters": len(chapters),
            },
        })

        # link units sequentially
        if ui > 0:
            prev_unit_node_id = f"unit_{units[ui - 1].id}"
            edges.append({
                "source": prev_unit_node_id,
                "target": unit_node_id,
                "label": "next workflow",
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "workflow_progress": {
            "completed_units": completed_units,
            "total_units": total_units,
            "completed_chapters": completed_chapters,
            "total_chapters": total_chapters,
        },
        "next_workflow": next_workflow,
    }


async def _unit_is_completed(db: AsyncSession, unit: Unit, user_id: uuid.UUID) -> bool:
    """A unit is complete when all of its chapters reach >= 0.8 confidence."""
    chapters = (await db.execute(
        select(Chapter).where(Chapter.unit_id == unit.id)
    )).scalars().all()
    if not chapters:
        return False
    for chapter in chapters:
        progress = await db.scalar(
            select(func.avg(LearningProgress.confidence)).where(
                LearningProgress.chapter_id == chapter.id,
                LearningProgress.user_id == user_id,
            )
        )
        if not progress or progress < 0.8:
            return False
    return True


# --- Unit Deep Exploration & Assessment ---
@router.get("/units/{unit_id}")
async def get_unit_detail(
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get a single unit with its subject metadata (user-scoped)."""
    unit_result = await db.execute(
        select(Unit, Subject)
        .join(Subject, Unit.subject_id == Subject.id)
        .where(Unit.id == unit_id, Subject.user_id == user.id)
    )
    row = unit_result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Unit not found")
    unit, subject = row[0], row[1]
    return {
        "unit": {
            "id": str(unit.id),
            "subject_id": str(unit.subject_id),
            "name": unit.name,
            "description": unit.description,
            "order": unit.order,
        },
        "subject": {
            "id": str(subject.id),
            "name": subject.name,
        },
    }


@router.post("/units/{unit_id}/explore")
async def explore_unit(
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Deep-exploration module for a workflow (unit). Cached in unit.exploration."""
    from app.services.ai_service import ai_provider

    unit_result = await db.execute(
        select(Unit, Subject.name)
        .join(Subject, Unit.subject_id == Subject.id)
        .where(Unit.id == unit_id, Subject.user_id == user.id)
    )
    row = unit_result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Unit not found")
    unit, course_name = row[0], row[1]

    if unit.exploration:
        return {"unit_id": str(unit.id), "content": unit.exploration, "cached": True}

    chapters = (await db.execute(
        select(Chapter).where(Chapter.unit_id == unit.id).order_by(Chapter.order)
    )).scalars().all()
    topics = (await db.execute(
        select(Topic).join(Chapter).where(Chapter.unit_id == unit.id).order_by(Chapter.order)
    )).scalars().all()

    outline = "\n".join(
        f"- {ch.name}: " + ", ".join(t.name for t in topics if t.chapter_id == ch.id)
        for ch in chapters
    ) or "(no chapters yet)"
    prompt = (
        "You are a subject-matter expert. Write a deep exploration module for the "
        "unit '{{UNIT}}' of the course '{{COURSE}}'. Cover: core concepts, how ideas "
        "connect, worked examples, common mistakes, and study tips. Output rich markdown "
        "with sections. Include at least 2 mermaid diagrams (fenced code blocks tagged "
        "```mermaid, e.g. flowchart, mindmap, or sequenceDiagram) to visualize the "
        "concepts, and at least 1 markdown table. Use $$...$$ for display math formulas. "
        "Base everything on this outline:\n{{OUTLINE}}"
    ).replace("{{UNIT}}", unit.name).replace("{{COURSE}}", course_name).replace("{{OUTLINE}}", outline)

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Unit description: {unit.description or 'none'}"},
    ]
    content = ""
    for _ in range(2):
        content = ""
        async for chunk in ai_provider.chat(messages, temperature=0.5, max_tokens=8192):
            data = json.loads(chunk)
            content += data.get("content", "")
        if content.strip():
            break

    if not content.strip():
        raise HTTPException(status_code=502, detail="AI unavailable — try again shortly (rate limit?)")

    unit.exploration = content
    await db.commit()
    return {"unit_id": str(unit.id), "content": content, "cached": False}


@router.post("/chapters/{chapter_id}/material")
async def generate_chapter_material(
    chapter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate the FULL detailed lesson material for a chapter (cached in chapter.material)."""
    from app.services.ai_service import ai_provider

    chapter_result = await db.execute(
        select(Chapter, Unit.name, Subject.name)
        .join(Unit, Chapter.unit_id == Unit.id)
        .join(Subject, Unit.subject_id == Subject.id)
        .where(Chapter.id == chapter_id, Subject.user_id == user.id)
    )
    row = chapter_result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Chapter not found")
    chapter, unit_name, course_name = row[0], row[1], row[2]

    if chapter.material:
        return {"chapter_id": str(chapter.id), "content": chapter.material, "cached": True}

    topics = (await db.execute(
        select(Topic).where(Topic.chapter_id == chapter.id).order_by(Topic.order)
    )).scalars().all()
    topic_outline = "\n".join(
        f"- {t.name}: {t.content or t.summary or ''}"
        for t in topics
    ) or "(no topics yet)"

    prompt = (
        "You are a world-class university professor. Write a COMPLETE, in-depth study "
        "lesson for the chapter '{{CHAPTER}}' of the unit '{{UNIT}}' in the course "
        "'{{COURSE}}'. This is a full teaching material, not a summary. Write in rich "
        "markdown and cover ALL of the following, in this order:\n"
        "## 1. Introduction\nWhy this matters and where it fits in the course.\n"
        "## 2. Core Concepts\nExplain every concept below in depth, with definitions, "
        "explanations, and context.\n"
        "## 3. Detailed Explanations\nGo deep into how the ideas work, step by step.\n"
        "## 4. Worked Examples\nAt least 2-3 fully worked examples with step-by-step "
        "solutions.\n"
        "## 5. Formulas & Key Points\nList all important formulas, laws, or key points.\n"
        "## 6. Common Mistakes\nTypical errors students make and how to avoid them.\n"
        "## 7. Practice Questions\n5 practice questions with answers.\n"
        "## 8. Key Takeaways\nBullet-point summary of what the student must remember.\n"
        "VISUAL CONTENT REQUIREMENTS (mandatory — the response MUST include these):\n"
        "- You MUST include at least 2 mermaid diagrams. Write them as fenced code blocks "
        "whose language tag is exactly 'mermaid' (a line ```mermaid, the diagram body, "
        "then ```). Use types like flowchart, mindmap, sequenceDiagram, or classDiagram. "
        "Keep each diagram 5-15 nodes with short labels. The ANSWER TEXT MUST CONTAIN "
        "THESE CODE BLOCKS — never describe a diagram without emitting it.\n"
        "- Include at least 1 markdown table comparing key concepts, formulas, or "
        "approaches.\n"
        "- Use markdown math notation for formulas: inline $formula$ and display "
        "$$formula$$ blocks (e.g. $$E = mc^2$$).\n"
        "- Use bold, bullet lists, and clear section headers to structure the material.\n"
        "Topics to cover in this chapter:\n{{TOPICS}}\n"
        "Write at least 800 words. Use markdown headings, bullet lists, and code/formula "
        "blocks where useful."
    ).replace("{{CHAPTER}}", chapter.name).replace("{{UNIT}}", unit_name).replace(
        "{{COURSE}}", course_name
    ).replace("{{TOPICS}}", topic_outline)

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Chapter description: {chapter.description or 'none'}"},
    ]
    content = ""
    for _ in range(2):
        content = ""
        async for chunk in ai_provider.chat(messages, temperature=0.5, max_tokens=8192):
            data = json.loads(chunk)
            content += data.get("content", "")
        if content.strip():
            break

    if not content.strip():
        raise HTTPException(status_code=502, detail="AI unavailable — try again shortly (rate limit?)")

    chapter.material = content
    await db.commit()
    return {"chapter_id": str(chapter.id), "content": content, "cached": False}


@router.post("/units/{unit_id}/assessment")
async def generate_unit_assessment(
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate an assessment (quiz) for a workflow (unit)."""
    from app.services.ai_service import ai_provider

    unit = await db.scalar(
        select(Unit)
        .join(Subject, Unit.subject_id == Subject.id)
        .where(Unit.id == unit_id, Subject.user_id == user.id)
    )
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    topics = (await db.execute(
        select(Topic).join(Chapter).where(Chapter.unit_id == unit.id).order_by(Chapter.order)
    )).scalars().all()
    content = "\n".join(f"{t.name}: {t.content or ''}" for t in topics) or unit.name

    questions = await ai_provider.generate_questions(
        content=content[:6000], question_type="mcq", count=5, difficulty="medium"
    )
    if not questions:
        raise HTTPException(status_code=502, detail="AI unavailable — try again shortly (rate limit?)")

    quiz = Quiz(
        user_id=user.id,
        subject_id=unit.subject_id,
        unit_id=unit.id,
        title=f"{unit.name} — Assessment",
        quiz_type="mcq",
        difficulty="medium",
        total_questions=len(questions),
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)

    for q in questions:
        db.add(Question(
            quiz_id=quiz.id,
            question_text=q.get("question_text", ""),
            question_type=q.get("question_type", "mcq"),
            options=q.get("options"),
            correct_answer=str(q.get("correct_answer", "")),
            explanation=q.get("explanation", ""),
            difficulty=q.get("difficulty", 1),
            marks=q.get("marks", 1),
        ))
    await db.commit()

    return {
        "quiz_id": str(quiz.id),
        "title": quiz.title,
        "total_questions": len(questions),
    }


# --- Study Plans ---
@router.post("/study-plans")
async def create_study_plan(
    data: StudyPlanRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    from app.services.ai_service import ai_provider

    plan = StudyPlan(
        user_id=user.id,
        title=data.title,
        description=data.description,
        exam_date=data.exam_date,
        daily_hours=data.daily_hours,
    )

    # Generate plan with AI
    if data.exam_date:
        days_remaining = (data.exam_date - datetime.utcnow()).days
        prompt = f"""Create a {days_remaining}-day study plan for {data.daily_hours} hours daily.
Organize into daily schedules with topics, breaks, and revision slots.
Return as JSON array of daily plans."""
        messages = [
            {"role": "system", "content": "You are a study plan generator. Return valid JSON only."},
            {"role": "user", "content": prompt},
        ]
        result = ""
        async for chunk in ai_provider.chat(messages, temperature=0.3):
            d = json.loads(chunk)
            result += d.get("content", "")
        try:
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            plan.plan_data = json.loads(result)
        except:
            plan.plan_data = {"error": "Failed to generate plan"}

    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return {"id": str(plan.id), "title": plan.title, "plan": plan.plan_data}


@router.get("/study-plans")
async def list_study_plans(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    from app.services.progress_service import get_progress_summary

    result = await db.execute(
        select(StudyPlan).where(StudyPlan.user_id == user.id).order_by(desc(StudyPlan.created_at))
    )
    plans = result.scalars().all()
    summary = await get_progress_summary(db, user.id)
    plan_progress = round(summary["overall"]["mastery"] / 100, 3)
    for p in plans:
        p.progress = plan_progress
    await db.commit()
    return [
        {
            "id": str(p.id),
            "title": p.title,
            "exam_date": p.exam_date,
            "daily_hours": p.daily_hours,
            "progress": p.progress,
            "is_active": p.is_active,
            "created_at": p.created_at,
        }
        for p in plans
    ]


# --- Study Sessions ---
@router.post("/study-sessions/start")
async def start_study_session(
    data: StudySessionStart,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    session = StudySession(
        user_id=user.id,
        subject_id=data.subject_id,
        session_type=data.session_type,
        started_at=datetime.utcnow(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"id": str(session.id), "started_at": session.started_at}


@router.post("/study-sessions/{session_id}/end")
async def end_study_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(StudySession).where(StudySession.id == session_id, StudySession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.ended_at = datetime.utcnow()
    if session.started_at:
        session.duration_minutes = int((session.ended_at - session.started_at).total_seconds() / 60)
    await db.commit()
    return {"id": str(session.id), "duration_minutes": session.duration_minutes}


# --- Memory System ---
@router.get("/memories", response_model=List[MemoryResponse])
async def get_memories(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(
        select(Memory).where(Memory.user_id == user.id).order_by(desc(Memory.importance), desc(Memory.recall_count))
    )
    memories = result.scalars().all()
    return [
        MemoryResponse(
            id=m.id, memory_type=m.memory_type, content=m.content,
            context=m.context, importance=m.importance, recall_count=m.recall_count,
            created_at=m.created_at,
        )
        for m in memories
    ]


@router.post("/memories/recall/{memory_id}")
async def recall_memory(
    memory_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Memory).where(Memory.id == memory_id, Memory.user_id == user.id)
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    memory.recall_count += 1
    memory.last_recalled = datetime.utcnow()
    # Spaced repetition: increase forgetting curve
    memory.forgetting_curve = memory.forgetting_curve * 0.9
    await db.commit()
    return {"message": "Memory recalled", "recall_count": memory.recall_count}


# --- Flashcards (Spaced Repetition) ---
@router.post("/flashcards/generate")
async def generate_flashcards(
    data: FlashcardGenerate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    from app.services.ai_service import ai_provider

    result = await db.execute(select(Subject).where(Subject.id == data.subject_id, Subject.user_id == user.id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    content = subject.description or subject.name
    chapters = await db.execute(select(Chapter).join(Unit).where(Unit.subject_id == data.subject_id))
    topics = await db.execute(select(Topic).join(Chapter).join(Unit).where(Unit.subject_id == data.subject_id))
    all_topics = topics.scalars().all()
    for t in all_topics:
        if t.content:
            content += "\n\n" + t.content[:1000]

    import re as _re

    def _clean_text(t: str) -> str:
        """Strip Unicode control/bidi chars and normalize whitespace."""
        # Remove U+200B..U+200F, U+2028..U+202E, U+2060..U+2069, U+FEFF, U+FFFC
        t = _re.sub(r'[\u200b-\u200f\u2028-\u202e\u2060-\u2069\ufeff\ufffc]', '', t)
        # Remove any surrogate pairs or non-BMP control chars
        t = _re.sub(r'[\U0001d173-\U0001d17a\U000e0001\U000e0020-\U000e007f]', '', t)
        # Collapse multiple spaces/newlines
        t = _re.sub(r'\s+', ' ', t).strip()
        return t

    prompt = (
        f"Create exactly {data.count} flashcards from the content below. "
        "Put the TERM or CONCEPT on 'front' and the DEFINITION or EXPLANATION on 'back'. "
        "Never swap them. Respond with valid JSON array only, each item with 'front' and 'back'. "
        "Use normal English letters only — no special Unicode, no reversed text."
    )
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": content[:5000]},
    ]
    result_text = ""
    async for chunk in ai_provider.chat(messages, temperature=0.1):
        import json as j
        data_chunk = j.loads(chunk)
        result_text += data_chunk.get("content", "")

    try:
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        cards_data = json.loads(result_text)
        if isinstance(cards_data, dict):
            cards_data = cards_data.get("flashcards", cards_data.get("cards", []))
    except Exception as e:
        logger.error(f"Flashcard parse error: {e} | raw: {result_text[:500]}")
        raise HTTPException(status_code=500, detail="Failed to generate flashcards")

    created = []
    for card_data in cards_data[:data.count]:
        front = _clean_text(card_data.get("front", card_data.get("question", "")))
        back = _clean_text(card_data.get("back", card_data.get("answer", "")))
        if not front or not back:
            continue
        if len(back) < len(front) * 0.4 and len(front) > 20:
            front, back = back, front
        card = Flashcard(
            user_id=user.id,
            front=front,
            back=back,
            next_review=datetime.utcnow(),
        )
        db.add(card)
        created.append({"front": front, "back": back})

    await db.commit()
    return {"flashcards": created, "count": len(created)}


@router.post("/flashcards")
async def create_flashcard(
    data: FlashcardCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    from datetime import timedelta
    card = Flashcard(
        user_id=user.id,
        topic_id=to_uuid(data.topic_id),
        front=data.front,
        back=data.back,
        next_review=datetime.utcnow(),
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return {
        "id": str(card.id),
        "front": card.front,
        "back": card.back,
        "next_review": card.next_review,
    }


@router.get("/flashcards/due")
async def get_due_flashcards(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Flashcard)
        .where(
            Flashcard.user_id == user.id,
            Flashcard.next_review <= datetime.utcnow(),
        )
        .order_by(Flashcard.next_review)
        .limit(limit)
    )
    cards = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "front": c.front,
            "back": c.back,
            "easiness": c.easiness,
            "interval": c.interval,
        }
        for c in cards
    ]


@router.post("/flashcards/{card_id}/review")
async def review_flashcard(
    card_id: uuid.UUID,
    quality: int,  # 0-5
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Flashcard).where(Flashcard.id == card_id, Flashcard.user_id == user.id)
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    # SM-2 Algorithm
    if quality >= 3:
        if card.repetitions == 0:
            card.interval = 1
        elif card.repetitions == 1:
            card.interval = 6
        else:
            card.interval = int(card.interval * card.easiness)
        card.repetitions += 1
    else:
        card.repetitions = 0
        card.interval = 1

    card.easiness = max(1.3, card.easiness + 0.1 - (5 - quality) * 0.08)
    from datetime import timedelta
    card.next_review = datetime.utcnow() + timedelta(days=card.interval)

    await db.commit()
    return {
        "id": str(card.id),
        "interval": card.interval,
        "easiness": card.easiness,
        "next_review": card.next_review,
    }


# --- Whiteboard ---
@router.post("/whiteboards")
async def create_whiteboard(
    data: WhiteboardCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    board = Whiteboard(user_id=user.id, name=data.name)
    db.add(board)
    await db.commit()
    await db.refresh(board)
    return {"id": str(board.id), "name": board.name}


@router.get("/whiteboards")
async def list_whiteboards(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(
        select(Whiteboard).where(Whiteboard.user_id == user.id).order_by(desc(Whiteboard.updated_at))
    )
    boards = result.scalars().all()
    return [{"id": str(b.id), "name": b.name, "updated_at": b.updated_at} for b in boards]


@router.put("/whiteboards/{board_id}")
async def update_whiteboard(
    board_id: uuid.UUID,
    data: WhiteboardUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Whiteboard).where(Whiteboard.id == board_id, Whiteboard.user_id == user.id)
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Whiteboard not found")
    if data.name is not None:
        board.name = data.name
    if data.elements is not None:
        board.elements = data.elements
    await db.commit()
    return {"id": str(board.id), "name": board.name}


@router.get("/whiteboards/{board_id}")
async def get_whiteboard(
    board_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Whiteboard).where(Whiteboard.id == board_id, Whiteboard.user_id == user.id)
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Whiteboard not found")
    return {
        "id": str(board.id),
        "name": board.name,
        "elements": board.elements,
        "is_collaborative": board.is_collaborative,
        "updated_at": board.updated_at,
    }

