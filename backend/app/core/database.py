from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

is_sqlite = "sqlite" in settings.DATABASE_URL

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def _migrate_sqlite(sync_conn):
    """Add columns introduced after the initial schema to existing SQLite DBs."""
    try:
        existing = {row[1] for row in sync_conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()}
        for col in ("education_level", "occupation", "domain"):
            if col not in existing:
                sync_conn.exec_driver_sql(f"ALTER TABLE users ADD COLUMN {col} VARCHAR(255)")
    except Exception:
        pass
    try:
        existing = {row[1] for row in sync_conn.exec_driver_sql("PRAGMA table_info(quizzes)").fetchall()}
        if "subject_id" not in existing:
            sync_conn.exec_driver_sql("ALTER TABLE quizzes ADD COLUMN subject_id CHAR(32)")
    except Exception:
        pass


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if is_sqlite:
            await conn.run_sync(_migrate_sqlite)