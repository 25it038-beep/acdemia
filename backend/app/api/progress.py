import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.auth import get_current_user
from app.services.progress_service import get_progress_summary

router = APIRouter(prefix="/api/progress", tags=["Progress"])


@router.get("/summary")
async def progress_summary(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await get_progress_summary(db, user.id)
