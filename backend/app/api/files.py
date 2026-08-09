import uuid
import os
import aiofiles
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from app.core.database import get_db
from app.core.config import settings
from app.models.models import File as FileModel, Subject, Project
from app.schemas.schemas import FileUploadResponse, SubjectResponse
from app.api.auth import get_current_user
from app.services.file_service import file_processor

router = APIRouter(prefix="/api/files", tags=["Files"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    subject_id: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported")

    # Create temp path
    upload_dir = os.path.join("uploads", str(user.id))
    os.makedirs(upload_dir, exist_ok=True)
    temp_path = os.path.join(upload_dir, f"{uuid.uuid4()}{ext}")

    # Save file
    async with aiofiles.open(temp_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Create file record
    file_record = FileModel(
        user_id=user.id,
        subject_id=uuid.UUID(subject_id) if subject_id else None,
        project_id=uuid.UUID(project_id) if project_id else None,
        original_filename=file.filename,
        stored_filename=os.path.basename(temp_path),
        file_type=ext[1:] if ext else "unknown",
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        status="uploaded",
    )
    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)

    # Process in background
    background_tasks.add_task(
        file_processor.process_file, file_record.id, temp_path, file_record.file_type
    )

    return FileUploadResponse(
        id=file_record.id,
        original_filename=file_record.original_filename,
        file_type=file_record.file_type,
        file_size=file_record.file_size,
        status=file_record.status,
        pages=file_record.pages,
        chunks=file_record.chunks,
        subject_id=file_record.subject_id,
        content_preview=(file_record.extracted_text or "")[:300],
        created_at=file_record.created_at,
    )


@router.get("/", response_model=List[FileUploadResponse])
async def list_files(
    subject_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    stmt = select(FileModel).where(FileModel.user_id == user.id)
    if subject_id:
        stmt = stmt.where(FileModel.subject_id == uuid.UUID(subject_id))
    stmt = stmt.order_by(FileModel.created_at.desc())
    result = await db.execute(stmt)
    files = result.scalars().all()
    return [
        FileUploadResponse(
            id=f.id,
            original_filename=f.original_filename,
            file_type=f.file_type,
            file_size=f.file_size,
            status=f.status,
            pages=f.pages,
            chunks=f.chunks,
            subject_id=f.subject_id,
            content_preview=(f.extracted_text or "")[:300],
            created_at=f.created_at,
        )
        for f in files
    ]


@router.delete("/{file_id}")
async def delete_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(FileModel).where(FileModel.id == file_id, FileModel.user_id == user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete physical file
    file_path = os.path.join("uploads", str(user.id), file.stored_filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    await db.delete(file)
    await db.commit()
    return {"message": "File deleted successfully"}