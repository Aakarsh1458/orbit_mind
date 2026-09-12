from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.models.analysis import AnalysisJob
from app.models.result import AnalysisResult
from app.schemas.response import AnalysisResultResponse

router = APIRouter(prefix="/api/v1/results", tags=["Results"])


@router.get(
    "/{job_id}",
    response_model=AnalysisResultResponse,
    summary="Get structured analysis result",
    description="Retrieves the final structured analysis result, evidence artifacts, geospatial statistics, and execution trace for a completed job."
)
async def get_analysis_result(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Verify job status
    job_stmt = select(AnalysisJob).where(AnalysisJob.id == job_id)
    job_res = await db.execute(job_stmt)
    job = job_res.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job '{job_id}' not found."
        )

    if job.status in ("queued", "processing"):
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Analysis job '{job_id}' is still in progress (status: {job.status}, progress: {job.progress * 100:.0f}%)."
        )

    if job.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis job '{job_id}' failed: {job.error}"
        )

    result_stmt = select(AnalysisResult).where(AnalysisResult.job_id == job_id)
    result_res = await db.execute(result_stmt)
    analysis_result = result_res.scalar_one_or_none()

    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Results for job '{job_id}' have not been generated."
        )

    return AnalysisResultResponse(
        job_id=analysis_result.job_id,
        analysis_type=job.analysis_type,
        mode=analysis_result.mode,
        summary=analysis_result.summary,
        confidence=analysis_result.confidence,
        statistics=analysis_result.statistics,
        evidence=analysis_result.evidence,
        execution_trace=analysis_result.execution_trace,
        created_at=analysis_result.created_at
    )


from app.core.config import settings
from app.core.security import validate_safe_path, SecurityException
from app.models.conversation import OrchestrationRun


@router.get(
    "/{job_id}/download/{filename:path}",
    summary="Download generated evidence artifact",
    description="Downloads the generated GeoTIFF change mask, segmentation raster, or composite for a specific analysis job or chat orchestration run."
)
async def download_evidence_file(
    job_id: str,
    filename: str,
    db: AsyncSession = Depends(get_db)
):
    # 1. Reject path traversal in filename parameter
    allowed_dirs = [
        Path(settings.RESULT_DIR).resolve(),
        Path(settings.PROCESSED_DIR).resolve(),
        Path(settings.UPLOAD_DIR).resolve(),
    ]

    try:
        # Validate that the requested filename itself does not have traversal components
        if ".." in filename or "/" in filename or "\\" in filename:
            raise SecurityException(f"Invalid filename: '{filename}'. Path traversal characters are forbidden.")
    except SecurityException as sec_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(sec_err.detail)
        )

    target_file: Optional[Path] = None

    # 2. Check AnalysisResult table
    result_stmt = select(AnalysisResult).where(AnalysisResult.job_id == job_id)
    result_res = await db.execute(result_stmt)
    analysis_result = result_res.scalar_one_or_none()

    if analysis_result and analysis_result.evidence:
        for k, v in analysis_result.evidence.items():
            if isinstance(v, str) and filename in v:
                cand = Path(v).resolve()
                if cand.exists():
                    target_file = cand
                    break

    # 3. Check OrchestrationRun table
    if not target_file:
        run_stmt = select(OrchestrationRun).where(OrchestrationRun.request_id == job_id)
        run_res = await db.execute(run_stmt)
        run = run_res.scalar_one_or_none()
        if run and run.result_path:
            cand = Path(run.result_path).resolve()
            if cand.name == filename and cand.exists():
                target_file = cand

    # 4. Check RESULT_DIR / PROCESSED_DIR / UPLOAD_DIR
    if not target_file:
        for base in allowed_dirs:
            cand = (base / filename).resolve()
            if cand.exists():
                target_file = cand
                break

    if not target_file or not target_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence artifact '{filename}' not found for request/job '{job_id}'."
        )

    # 5. Final boundary security verification
    try:
        safe_target = validate_safe_path(target_file, allowed_base_dirs=allowed_dirs)
    except SecurityException as sec_err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(sec_err.detail)
        )

    media_type = "image/tiff" if safe_target.suffix in (".tif", ".tiff") else "application/octet-stream"
    return FileResponse(
        path=str(safe_target),
        filename=safe_target.name,
        media_type=media_type
    )

