import os
import uuid
import logging
import asyncio
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.config import settings
from app.core.database import get_db
from app.models.models import File, Chunk, Subject, Unit, Chapter, Topic, Concept

logger = logging.getLogger(__name__)


class FileProcessor:
    """Handles the complete file processing pipeline."""

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

                # Step 3: Chunk the text
                chunks = self._chunk_text(extracted_text, file_type)
                logger.info(f"Created {len(chunks)} chunks for file {file_id}")

                # Step 4: Generate embeddings and store chunks
                embedded_chunks = []
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
                    embedded_chunks.append((chunk, embedding))

                await db.commit()

                # Step 5: Store embeddings in Qdrant (skip if unavailable)
                try:
                    from app.services.vector_service import vector_store
                    for chunk, embedding in embedded_chunks:
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
                except Exception as qe:
                    logger.warning(f"Qdrant unavailable, skipping vector storage: {qe}")

                # Step 6: Auto-detect subject and organize
                await self._auto_organize(db, file_id, extracted_text)

                # Step 7: Mark as completed
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
            async for chunk in ai_provider.chat(messages, temperature=0.3):
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

    async def _update_status(self, db: AsyncSession, file_id: uuid.UUID, status: str):
        stmt = update(File).where(File.id == file_id).values(status=status)
        await db.execute(stmt)
        await db.commit()


file_processor = FileProcessor()