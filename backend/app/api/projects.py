import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.core.database import get_db
from app.models.models import Project, Task, File
from app.schemas.schemas import ProjectCreate, ProjectResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(
        select(Project).where(Project.user_id == user.id).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            status=p.status,
            technologies=p.technologies or [],
            difficulty=p.difficulty,
            score=p.score,
            progress=0.0,
            deadline=p.deadline,
            created_at=p.created_at,
        )
        for p in projects
    ]


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    project = Project(
        user_id=user.id,
        name=data.name,
        description=data.description,
        technologies=data.technologies or [],
        difficulty=data.difficulty,
        deadline=data.deadline,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        technologies=project.technologies or [],
        difficulty=project.difficulty,
        score=project.score,
        progress=0.0,
        deadline=project.deadline,
        created_at=project.created_at,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        technologies=project.technologies or [],
        difficulty=project.difficulty,
        score=project.score,
        progress=0.0,
        deadline=project.deadline,
        created_at=project.created_at,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.name = data.name
    project.description = data.description
    project.technologies = data.technologies or []
    project.difficulty = data.difficulty
    project.deadline = data.deadline
    await db.commit()
    await db.refresh(project)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        technologies=project.technologies or [],
        difficulty=project.difficulty,
        score=project.score,
        progress=0.0,
        deadline=project.deadline,
        created_at=project.created_at,
    )


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
