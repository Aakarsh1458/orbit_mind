from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.models.analysis import AnalysisJob
from app.schemas.analysis import JobStatusResponse

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.get(
    "",
    response_model=List[JobStatusResponse],
    summary="List analysis jobs",
    description="Retrieves a list of recent analysis jobs."
)
async def list_jobs(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AnalysisJob).order_by(AnalysisJob.created_at.desc()).offset(offset).limit(limit)
    res = await db.execute(stmt)
    jobs = res.scalars().all()
    return [
        JobStatusResponse(
            job_id=job.id,
            query=job.query,
            analysis_type=job.analysis_type,
            status=job.status,
            progress=job.progress,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error=job.error
        )
        for job in jobs
    ]


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job execution status",
    description="Retrieves the current execution lifecycle status (queued, processing, completed, failed), progress percentage, and timestamps for an analysis job."
)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AnalysisJob).where(AnalysisJob.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job with ID '{job_id}' not found."
        )

    return JobStatusResponse(
        job_id=job.id,
        query=job.query,
        analysis_type=job.analysis_type,
        status=job.status,
        progress=job.progress,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error=job.error
    )
