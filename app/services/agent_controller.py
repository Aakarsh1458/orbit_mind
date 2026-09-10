from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.registry import model_registry
from app.core.config import settings
from app.core.logging import logger
from app.services.query_service import query_service
from app.services.imagery_service import imagery_service
from app.services.preprocessing_service import preprocessing_service
from app.services.evidence_service import evidence_service
from app.services.statistics_service import statistics_service
from app.models.imagery import Imagery


class OrbitMindAgentController:
    """
    Central orchestration controller for OrbitMind.
    Coordinates query understanding, imagery validation, geospatial alignment,
    specialist model dispatch, and structured evidence compilation.
    """

    def __init__(self, mode: Optional[str] = None):
        self.mode = (mode or settings.AI_MODE).lower()

    async def execute_analysis_pipeline(
        self,
        imagery_ids: List[str],
        query: Optional[str] = None,
        explicit_analysis_type: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        execution_trace = []
        out_dir = (output_dir or Path(settings.RESULT_DIR)).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Query Understanding & Intent Classification
        execution_trace.append("query_understanding")
        if explicit_analysis_type:
            analysis_type = explicit_analysis_type.lower().strip()
            logger.info("Using explicitly specified analysis_type: %s", analysis_type)
        elif query:
            understanding = query_service.understand_query(query)
            analysis_type = understanding["selected_analysis"]
            logger.info("Inferred analysis_type '%s' from query: '%s'", analysis_type, query)
        else:
            # Default fallback based on image count
            analysis_type = "change_detection" if len(imagery_ids) >= 2 else "captioning"
            logger.info("No query or analysis_type provided. Defaulting to '%s'", analysis_type)

        # Step 2: Imagery Validation
        execution_trace.append("imagery_validation")
        imagery_records: List[Imagery] = []
        if db:
            for img_id in imagery_ids:
                rec = await imagery_service.get_imagery_by_id(img_id, db)
                if not rec:
                    raise ValueError(f"Imagery ID '{img_id}' not found in database records.")
                imagery_records.append(rec)
        else:
            # Fallback if executing directly with filepaths
            for path_str in imagery_ids:
                p = Path(path_str)
                if not p.exists():
                    raise FileNotFoundError(f"Imagery path not found: {path_str}")
                # Mock minimal record
                from app.geospatial.raster import read_raster_metadata
                meta = read_raster_metadata(p)
                fake_rec = Imagery(
                    id=p.stem,
                    filename=p.name,
                    path=str(p),
                    crs=meta["crs"],
                    width=meta["width"],
                    height=meta["height"],
                    bands=meta["bands"],
                    bounds=meta["bounds"],
                    resolution=meta["resolution"],
                    is_georeferenced=meta.get("is_georeferenced", True),
                    file_size_bytes=p.stat().st_size
                )
                imagery_records.append(fake_rec)

        # Step 3: Geospatial Preprocessing & Alignment
        execution_trace.append("geospatial_preprocessing")
        prepared_paths = preprocessing_service.validate_and_prepare_inputs(
            analysis_type=analysis_type,
            imagery_records=imagery_records,
            output_dir=out_dir
        )

        # Step 4: Specialist Model Selection & Inference
        execution_trace.append(analysis_type)
        model = model_registry.get_model(analysis_type, mode=self.mode)
        
        inputs = {
            "query": query,
            "imagery_paths": prepared_paths,
            "output_dir": str(out_dir)
        }
        
        raw_result = model.predict(inputs)

        # Step 5: Statistics Compilation
        execution_trace.append("statistics")
        formatted_stats = statistics_service.format_statistics(raw_result.get("statistics", {}))

        # Step 6: Evidence Generation
        execution_trace.append("evidence_generation")
        evidence = evidence_service.compile_evidence(raw_result, prepared_paths)

        # Final structured payload
        return {
            "analysis_type": analysis_type,
            "mode": self.mode,
            "summary": raw_result.get("summary", ""),
            "confidence": raw_result.get("confidence", 0.0),
            "statistics": formatted_stats,
            "evidence": evidence,
            "execution_trace": execution_trace,
            "result_path": evidence.get("change_mask") or evidence.get("segmentation_mask") or evidence.get("fused_raster")
        }


agent_controller = OrbitMindAgentController()
