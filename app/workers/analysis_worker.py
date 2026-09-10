import traceback
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import logger
from app.models.database import async_session_factory
from app.models.analysis import AnalysisJob
from app.models.result import AnalysisResult
from app.services.agent_controller import agent_controller


async def run_analysis_worker(job_id: str) -> None:
    """
    Background worker task executing remote-sensing analysis pipeline for a job.
    Updates job progress and persists structured analysis result.
    Can be dispatched directly via FastAPI BackgroundTasks or by Celery/RQ worker.
    """
    logger.info("Starting background analysis worker for Job ID: %s", job_id)

    async with async_session_factory() as db:
        stmt = select(AnalysisJob).where(AnalysisJob.id == job_id)
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()

        if not job:
            logger.error("Job %s not found in database. Aborting worker.", job_id)
            return

        if job.status == "completed":
            logger.info("Job %s is already completed. Skipping.", job_id)
            return

        try:
            # Mark processing
            job.status = "processing"
            job.progress = 0.15
            job.started_at = datetime.now(timezone.utc)
            await db.commit()

            # Execute pipeline
            pipeline_result = await agent_controller.execute_analysis_pipeline(
                imagery_ids=job.imagery_ids,
                query=job.query,
                explicit_analysis_type=job.analysis_type,
                db=db,
                output_dir=Path(settings.RESULT_DIR)
            )

            job.progress = 0.85
            await db.commit()

            # Check if result was already persisted
            res_check = await db.execute(select(AnalysisResult).where(AnalysisResult.job_id == job.id))
            existing_result = res_check.scalar_one_or_none()

            if not existing_result:
                analysis_result = AnalysisResult(
                    job_id=job.id,
                    summary=pipeline_result["summary"],
                    confidence=pipeline_result["confidence"],
                    mode=pipeline_result["mode"],
                    statistics=pipeline_result["statistics"],
                    evidence=pipeline_result["evidence"],
                    execution_trace=pipeline_result["execution_trace"],
                    result_path=pipeline_result.get("result_path")
                )
                db.add(analysis_result)

            # Mark completed
            job.status = "completed"
            job.progress = 1.0
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info("Successfully completed analysis job %s", job_id)

        except Exception as exc:
            logger.error("Error processing analysis job %s: %s\n%s", job_id, exc, traceback.format_exc())
            job.status = "failed"
            job.error = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()
