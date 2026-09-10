import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.logging import logger
from app.models.analysis import AnalysisJob
from app.schemas.analysis import AnalysisRequest, AnalysisJobResponse
from app.services.query_service import query_service
from app.services.imagery_service import imagery_service
from app.workers.analysis_worker import run_analysis_worker

router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])


@router.post(
    "",
    response_model=AnalysisJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start an analysis job",
    description="Asynchronously starts a remote sensing analysis job (e.g. change detection, segmentation, VQA). Immediately returns job_id with 'queued' status."
)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    if not request.imagery_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one imagery_id must be provided."
        )

    # Validate that all imagery records exist
    for img_id in request.imagery_ids:
        rec = await imagery_service.get_imagery_by_id(img_id, db)
        if not rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Referenced imagery_id '{img_id}' not found."
            )

    # Determine analysis type
    if request.analysis_type:
        analysis_type = request.analysis_type.lower().strip()
    elif request.query:
        understanding = query_service.understand_query(request.query)
        analysis_type = understanding["selected_analysis"]
    else:
        analysis_type = "change_detection" if len(request.imagery_ids) >= 2 else "captioning"

    # Create job in database
    job = AnalysisJob(
        id=str(uuid.uuid4()),
        query=request.query,
        analysis_type=analysis_type,
        imagery_ids=request.imagery_ids,
        status="queued",
        progress=0.0,
        created_at=datetime.now(timezone.utc)
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Schedule asynchronous worker
    background_tasks.add_task(run_analysis_worker, job.id)
    logger.info("Enqueued background analysis job %s (type: %s)", job.id, analysis_type)

    return AnalysisJobResponse(
        job_id=job.id,
        status=job.status,
        analysis_type=job.analysis_type,
        created_at=job.created_at
    )
