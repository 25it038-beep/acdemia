import asyncio
import logging
from app.services.file_service import file_processor
from app.core.database import async_session_factory
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_file_task(self, file_id: str, file_path: str, file_type: str):
    """Background task for file processing."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def process():
            async with async_session_factory() as db:
                import uuid
                await file_processor.process_file(
                    db, uuid.UUID(file_id), file_path, file_type
                )
        loop.run_until_complete(process())
        loop.close()
        return {"status": "completed", "file_id": file_id}
    except Exception as e:
        logger.error(f"Task failed: {e}")
        self.retry(exc=e, countdown=60)


@celery_app.task
def generate_embeddings_task(texts: list):
    """Generate embeddings in background."""
    from app.services.ai_service import ai_provider
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    embeddings = loop.run_until_complete(ai_provider.generate_embeddings(texts))
    loop.close()
    return embeddings


@celery_app.task
def cleanup_old_files():
    """Periodic cleanup of temporary files."""
    import os
    import shutil
    upload_dir = "uploads"
    if os.path.exists(upload_dir):
        for user_dir in os.listdir(upload_dir):
            user_path = os.path.join(upload_dir, user_dir)
            if os.path.isdir(user_path):
                shutil.rmtree(user_path)
                logger.info(f"Cleaned up {user_path}")