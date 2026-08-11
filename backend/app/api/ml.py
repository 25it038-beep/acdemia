import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.core.database import get_db
from app.models.models import File as FileModel
from app.api.auth import get_current_user
from app.schemas.schemas import MLAnalysisResponse, SimilarFileResponse
from app.services.ml_service import analyze_document, find_similar_documents

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])
logger = logging.getLogger(__name__)


@router.get("/analyze/{file_id}", response_model=MLAnalysisResponse)
async def analyze_file(
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

    analysis = file.ml_analysis or {}
    if analysis.get("status") != "complete" or not analysis.get("keywords"):
        if not file.extracted_text or not file.extracted_text.strip():
            raise HTTPException(
                status_code=422,
                detail="No extractable text in this file, ML analysis unavailable",
            )
        analysis = analyze_document(file.extracted_text, keyword_count=10)
        file.ml_analysis = analysis
        await db.commit()

    return MLAnalysisResponse(
        file_id=file.id,
        filename=file.original_filename,
        file_type=file.file_type,
        status=analysis.get("status"),
        statistics=analysis.get("statistics", {}),
        readability=analysis.get("readability", {}),
        difficulty=analysis.get("difficulty", {}),
        keywords=analysis.get("keywords", []),
        subject_matches=analysis.get("subject_matches", []),
    )


@router.get("/similar/{file_id}", response_model=List[SimilarFileResponse])
async def similar_files(
    file_id: uuid.UUID,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    limit = max(1, min(limit, 20))
    result = await db.execute(
        select(FileModel).where(FileModel.id == file_id, FileModel.user_id == user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if not file.extracted_text or not file.extracted_text.strip():
        raise HTTPException(status_code=422, detail="File has no extractable text")

    result = await db.execute(
        select(FileModel)
        .options(selectinload(FileModel.subject))
        .where(
            FileModel.user_id == user.id,
            FileModel.id != file_id,
            FileModel.status == "completed",
            FileModel.extracted_text.isnot(None),
        )
    )
    others = result.scalars().all()
    if not others:
        return []

    candidates = [
        {
            "id": f.id,
            "title": f.original_filename,
            "text": f.extracted_text[:20000] or "",
            "file_type": f.file_type,
            "pages": f.pages,
            "subject": f.subject.name if f.subject else None,
        }
        for f in others
    ]
    similar = find_similar_documents(
        file.extracted_text[:50000], candidates, top_n=limit
    )
    return [SimilarFileResponse(**s) for s in similar]
