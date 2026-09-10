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


@router.get(
    "/{job_id}/download/{filename}",
    summary="Download generated evidence artifact",
    description="Downloads the generated GeoTIFF change mask, segmentation raster, or composite for a specific analysis job."
)
async def download_evidence_file(
    job_id: str,
    filename: str,
    db: AsyncSession = Depends(get_db)
):
    result_stmt = select(AnalysisResult).where(AnalysisResult.job_id == job_id)
    result_res = await db.execute(result_stmt)
    analysis_result = result_res.scalar_one_or_none()

    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Result for job '{job_id}' not found."
        )

    # Search evidence dictionary for matching file
    evidence = analysis_result.evidence
    candidate_paths = []
    for k, v in evidence.items():
        if isinstance(v, str) and filename in v:
            candidate_paths.append(v)

    if not candidate_paths:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence artifact '{filename}' not found in job results."
        )

    target_file = Path(candidate_paths[0]).resolve()
    if not target_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence file does not exist on disk: {filename}"
        )

    media_type = "image/tiff" if target_file.suffix in (".tif", ".tiff") else "application/octet-stream"
    return FileResponse(
        path=str(target_file),
        filename=target_file.name,
        media_type=media_type
    )
