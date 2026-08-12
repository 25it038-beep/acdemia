import os
import uuid
import logging
import asyncio
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.core.config import settings
from app.core.database import get_db
from app.models.models import File, Chunk, Subject, Unit, Chapter, Topic, Concept

logger = logging.getLogger(__name__)


class FileProcessor:
    """Handles the complete file processing pipeline."""

    _qdrant_probed = False
    _qdrant_ok = False

    async def _qdrant_available(self) -> bool:
        """Probe Qdrant once per process and cache the result."""
        if self._qdrant_probed:
            return self._qdrant_ok
        self._qdrant_probed = True
        try:
            from app.services.vector_service import vector_store
            if vector_store.client is None:
                return False
            await vector_store.ensure_collection()
            self._qdrant_ok = True
        except Exception as e:
            logger.warning(f"Qdrant unavailable, vector search disabled: {e}")
        return self._qdrant_ok

    async def process_file(
        self, file_id: uuid.UUID, file_path: str, file_type: str
    ) -> None:
        from app.services.ai_service import ai_provider
        from app.core.database import async_session_factory

        async with async_session_factory() as db:
            try:
                await self._update_status(db, file_id, "processing")

                # Step 1: Text extraction
                logger.info(f"Extracting text from {file_path}")
                extracted_text = await ai_provider.extract_text_from_file(file_path, file_type)

                # Step 2: Update file with extracted text
                stmt = (
                    update(File)
                    .where(File.id == file_id)
                    .values(extracted_text=extracted_text, status="text_extracted")
                )
                await db.execute(stmt)
                await db.commit()

                # Step 2b: Machine-learning analysis (keywords, subject
                # classification, readability, difficulty) — pure offline NLP
                ml_result = {}
                if extracted_text and extracted_text.strip():
                    try:
                        from app.services.ml_service import analyze_document
                        ml_result = analyze_document(
                            extracted_text,
                            corpus=[extracted_text],
                            keyword_count=10,
                        )
                        stmt = (
                            update(File)
                            .where(File.id == file_id)
                            .values(ml_analysis=ml_result)
                        )
                        await db.execute(stmt)
                        await db.commit()
                    except Exception as mle:
                        logger.warning(f"ML analysis failed for {file_id}: {mle}")
                        await db.rollback()

                # Step 3: Build the course workflow from the content (fast path —
                # users see units/chapters right away)
                await self._auto_organize(db, file_id, extracted_text)

                # Step 4: Chunk the text (kept cheap; counts are shown in the UI)
                chunks = self._chunk_text(extracted_text, file_type)
                logger.info(f"Created {len(chunks)} chunks for file {file_id}")

                # Step 5: Embeddings + Qdrant — only when Qdrant is actually up
                qdrant_ok = await self._qdrant_available()
                if qdrant_ok:
                    try:
                        from app.services.vector_service import vector_store
                        chunk_texts = [c["content"] for c in chunks]
                        embeddings = await ai_provider.generate_embeddings(chunk_texts)
                        for i, (chunk_data, embedding) in enumerate(zip(chunks, embeddings)):
                            chunk = Chunk(
                                file_id=file_id,
                                content=chunk_data["content"],
                                chunk_index=i,
                                chunk_type=chunk_data.get("type", "text"),
                                extra_metadata=chunk_data.get("metadata", {}),
                            )
                            db.add(chunk)
                            await db.flush()
                            await vector_store.upsert(
                                collection_name="academia",
                                point_id=str(chunk.id),
                                vector=embedding,
                                payload={
                                    "file_id": str(file_id),
                                    "content": chunk.content[:500],
                                    "chunk_index": chunk.chunk_index,
                                },
                            )
                        await db.commit()
                    except Exception as qe:
                        logger.warning(f"Vector storage skipped: {qe}")
                        await db.rollback()

                # Step 6: Mark as completed
                stmt = (
                    update(File)
                    .where(File.id == file_id)
                    .values(
                        status="completed",
                        chunks=len(chunks),
                    )
                )
                await db.execute(stmt)
                await db.commit()

                logger.info(f"File {file_id} processed successfully")

            except Exception as e:
                logger.error(f"File processing error for {file_id}: {e}")
                stmt = (
                    update(File)
                    .where(File.id == file_id)
                    .values(status="error", error_message=str(e))
                )
                await db.execute(stmt)
                await db.commit()

    def _chunk_text(self, text: str, file_type: str, chunk_size: int = 1000) -> List[dict]:
        """Split text into semantic chunks."""
        if not text.strip():
            return [{"content": "No text content extracted.", "type": "empty"}]

        chunks = []
        paragraphs = text.split("\n\n")
        current_chunk = ""
        current_type = "text"

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append({
                    "content": current_chunk.strip(),
                    "type": current_type,
                    "metadata": {"length": len(current_chunk)},
                })
                current_chunk = ""
                current_type = "text"

            current_chunk += para + "\n\n"

            # Detect chunk type
            if any(kw in para.lower() for kw in ["formula", "equation", "\\[", "\\(", "$$"]):
                current_type = "formula"
            elif any(kw in para.lower() for kw in ["code", "def ", "class ", "function", "import "]):
                current_type = "code"
            elif any(kw in para.lower() for kw in ["table", "|", "column"]):
                current_type = "table"

        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "type": current_type,
                "metadata": {"length": len(current_chunk)},
            })

        return chunks if chunks else [{"content": text, "type": "text", "metadata": {}}]

    async def _auto_organize(self, db: AsyncSession, file_id: uuid.UUID, text: str) -> None:
        """Auto-detect and create subject, units, chapters, topics, and concepts from content."""
        from app.services.ai_service import ai_provider

        result = await db.execute(select(File).where(File.id == file_id))
        file = result.scalar_one_or_none()
        if not file:
            return

        # Skip AI analysis for files with no extractable text (images, video, audio)
        if not text.strip() or text.startswith("[") and text.endswith("]"):
            logger.info(f"Skipping auto-organization for file {file_id} (no extractable text)")
            return

        if not file.subject_id:
            prompt = (
                "Analyze the following educational content and respond with valid JSON only:\n"
                "{\n"
                '  "subject": "Subject name",\n'
                '  "units": [\n'
                '    {\n'
                '      "name": "Unit name",\n'
                '      "chapters": [\n'
                '        {\n'
                '          "name": "Chapter name",\n'
                '          "topics": [\n'
                '            {\n'
                '              "name": "Topic name",\n'
                '              "content": "Brief description of this topic"\n'
                '            }\n'
                '          ]\n'
                '        }\n'
                '      ]\n'
                '    }\n'
                '  ],\n'
                '  "concepts": [\n'
                '    {"name": "Concept name", "definition": "Brief definition", "importance": 5}\n'
                '  ]\n'
                "}"
            )
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text[:4000]},
            ]
            result_text = ""
            async for chunk in ai_provider.chat(messages, temperature=0.3, task="coding"):
                import json as j
                data = j.loads(chunk)
                result_text += data.get("content", "")

            try:
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()

                import json as j
                info = j.loads(result_text)

                subject_name = info.get("subject", "Unknown Subject")
                stmt = select(Subject).where(
                    Subject.user_id == file.user_id,
                    Subject.name.ilike(f"%{subject_name}%"),
                )
                result_subj = await db.execute(stmt)
                subject = result_subj.scalar_one_or_none()

                if not subject:
                    subject = Subject(
                        user_id=file.user_id,
                        name=subject_name,
                        description=f"Auto-detected from {file.original_filename}",
                    )
                    db.add(subject)
                    await db.commit()
                    await db.refresh(subject)

                file.subject_id = subject.id

                # Create units -> chapters -> topics
                for unit_data in info.get("units", []):
                    unit = Unit(
                        subject_id=subject.id,
                        name=unit_data.get("name", "Unit"),
                        order=info.get("units", []).index(unit_data),
                    )
                    db.add(unit)
                    await db.flush()

                    for ch_data in unit_data.get("chapters", []):
                        chapter = Chapter(
                            unit_id=unit.id,
                            name=ch_data.get("name", "Chapter"),
                            order=unit_data.get("chapters", []).index(ch_data),
                        )
                        db.add(chapter)
                        await db.flush()

                        for tp_data in ch_data.get("topics", []):
                            topic = Topic(
                                chapter_id=chapter.id,
                                name=tp_data.get("name", "Topic"),
                                content=tp_data.get("content", text[:500]),
                                order=ch_data.get("topics", []).index(tp_data),
                            )
                            db.add(topic)
                            await db.flush()

                # Create concepts linked to first topic
                first_topic = await db.scalar(
                    select(Topic).join(Chapter).join(Unit).where(
                        Unit.subject_id == subject.id
                    ).limit(1)
                )
                for c_data in info.get("concepts", []):
                    concept = Concept(
                        topic_id=first_topic.id if first_topic else None,
                        name=c_data.get("name", "Concept"),
                        definition=c_data.get("definition", ""),
                        importance=c_data.get("importance", 5),
                    )
                    db.add(concept)

                await db.commit()

                if info.get("units"):
                    await self._notify_workflow_ready(
                        db,
                        subject,
                        f"Course structure for \"{file.original_filename}\" is ready. Open the workflow to start learning.",
                        user_id=file.user_id,
                    )

                # Push to Neo4j if available
                try:
                    from app.services.knowledge_service import knowledge_graph
                    if knowledge_graph.driver:
                        for c_data in info.get("concepts", []):
                            await knowledge_graph.add_concept(
                                concept_id=str(uuid.uuid4()),
                                name=c_data.get("name", ""),
                                topic=subject.name,
                                difficulty=1,
                                importance=c_data.get("importance", 5),
                            )
                except Exception:
                    pass

            except Exception as e:
                logger.warning(f"Auto-organization failed: {e}")
                await db.rollback()
        else:
            await self._organize_existing_subject(db, file, text)

    async def _notify_workflow_ready(
        self, db: AsyncSession, subject: Subject, message: str, user_id: uuid.UUID
    ) -> None:
        """Notify the user that a workflow was generated."""
        try:
            from app.api.notifications import create_notification
            await create_notification(
                db,
                user_id=user_id,
                title="Workflow generated",
                message=message,
                notification_type="success",
                action_url=f"/workflow?subject={subject.id}",
            )
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to create workflow notification: {e}")

    def _build_course_context(self, subject: Subject) -> str:
        """Course metadata + syllabus to guide workflow generation."""
        import json as j
        parts = []
        if subject.description:
            parts.append(f"Description: {subject.description}")
        if subject.university:
            parts.append(f"University: {subject.university}")
        if subject.semester:
            parts.append(f"Semester: {subject.semester}")
        if subject.subject_code:
            parts.append(f"Course code: {subject.subject_code}")
        if subject.syllabus:
            parts.append(f"Syllabus: {j.dumps(subject.syllabus, indent=2)[:1500]}")
        return "\n".join(parts)

    async def _generate_for_subject(
        self, db: AsyncSession, subject: Subject, user_content: str, source: str
    ) -> None:
        """Run NVIDIA-based structure generation for a subject (shared by file/course paths)."""
        from app.services.ai_service import ai_provider
        import json as j

        prompt = (
            "You are a curriculum designer. Build the course workflow for "
            "'{{COURSE_NAME}}' from the provided course information and material. "
            "Respond with valid JSON only, exactly this shape (NO markdown fences):\n"
            "{\n"
            '  "units": [\n'
            '    {\n'
            '      "name": "Unit name",\n'
            '      "description": "Short description",\n'
            '      "chapters": [\n'
            '        {\n'
            '          "name": "Chapter name",\n'
            '          "estimated_hours": 2.0,\n'
            '          "difficulty": 2,\n'
            '          "topics": [\n'
            '            {\n'
            '              "name": "Topic name",\n'
            '              "content": "Brief summary of this topic"\n'
            '            }\n'
            '          ]\n'
            '        }\n'
            '      ]\n'
            '    }\n'
            '  ]\n'
            "}\n"
            "Cover the full scope of the course. Split it into logical units (modules) "
            "and chapters (lessons) with 2-6 topics each. Estimated hours 1-4, "
            "difficulty 1-5."
        ).replace("{{COURSE_NAME}}", subject.name)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content},
        ]

        result_text = ""
        async for chunk in ai_provider.chat(messages, temperature=0.3, task="coding"):
            data = j.loads(chunk)
            result_text += data.get("content", "")

        try:
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            info = j.loads(result_text)

            for unit_data in info.get("units", []):
                unit = Unit(
                    subject_id=subject.id,
                    name=unit_data.get("name", "Unit"),
                    description=unit_data.get("description"),
                    order=info.get("units", []).index(unit_data),
                )
                db.add(unit)
                await db.flush()

                for ch_data in unit_data.get("chapters", []):
                    chapter = Chapter(
                        unit_id=unit.id,
                        name=ch_data.get("name", "Chapter"),
                        description=ch_data.get("description"),
                        order=unit_data.get("chapters", []).index(ch_data),
                        estimated_hours=ch_data.get("estimated_hours", 1.0),
                        difficulty=ch_data.get("difficulty", 1),
                    )
                    db.add(chapter)
                    await db.flush()

                    for tp_data in ch_data.get("topics", []):
                        topic = Topic(
                            chapter_id=chapter.id,
                            name=tp_data.get("name", "Topic"),
                            content=tp_data.get("content", user_content[:500]),
                            order=ch_data.get("topics", []).index(tp_data),
                        )
                        db.add(topic)
                        await db.flush()

            await db.commit()
            count = len(info.get("units", []))
            logger.info(f"Generated {count} units for subject {subject.id} from {source}")
            if count:
                await self._notify_workflow_ready(
                    db,
                    subject,
                    f"Course structure for \"{subject.name}\" is ready. Open the workflow to start learning.",
                    user_id=subject.user_id,
                )
        except Exception as e:
            logger.warning(f"Workflow generation failed for subject {subject.id}: {e}")
            await db.rollback()

    async def _organize_existing_subject(
        self, db: AsyncSession, file: File, text: str
    ) -> None:
        """Generate units/chapters/topics for a course combining course info + file content."""
        result = await db.execute(select(Subject).where(Subject.id == file.subject_id))
        subject = result.scalar_one_or_none()
        if not subject:
            return

        existing_units = await db.scalar(
            select(func.count(Unit.id)).where(Unit.subject_id == subject.id)
        )
        if existing_units:
            logger.info(f"Subject {subject.id} already has units, skipping generation")
            return

        context = self._build_course_context(subject)
        if context:
            user_content = (
                f"Course information:\n{context}\n\n"
                f"Material from \"{file.original_filename}\":\n{text[:5000]}"
            )
        else:
            user_content = f"Material from \"{file.original_filename}\":\n{text[:5000]}"

        await self._generate_for_subject(
            db, subject, user_content, f"file {file.original_filename}"
        )

    async def organize_from_course(self, subject_id: uuid.UUID) -> None:
        """Generate a workflow from course info alone (on creation or manual trigger)."""
        from app.core.database import async_session_factory

        async with async_session_factory() as db:
            subject = await db.get(Subject, subject_id)
            if not subject:
                return
            existing_units = await db.scalar(
                select(func.count(Unit.id)).where(Unit.subject_id == subject.id)
            )
            if existing_units:
                return
            context = self._build_course_context(subject)
            user_content = (
                f"Course information:\n{context}\n\n"
                f"Course name: {subject.name}"
                if context else
                f"Build the workflow for the course: {subject.name}"
            )
            await self._generate_for_subject(
                db, subject, user_content, "course info"
            )

    async def _update_status(self, db: AsyncSession, file_id: uuid.UUID, status: str):
        stmt = update(File).where(File.id == file_id).values(status=status)
        await db.execute(stmt)
        await db.commit()


file_processor = FileProcessor()