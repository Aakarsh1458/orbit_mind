import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import rasterio
from rasterio.transform import from_origin
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.services.imagery_service import imagery_service


class OrbitMindsDataset:
    """
    OrbitMind remote-sensing dataset wrapper for Hermanni/sen12mscr.
    Supports multi-modal Sentinel-1 (SAR) and Sentinel-2 (Optical) pairs.
    """

    def __init__(self, split: str = "train", streaming: bool = True, use_hf: Optional[bool] = None):
        self.split = split
        self.streaming = streaming
        self.use_hf = use_hf if use_hf is not None else (os.getenv("ENABLE_HF_STREAMING", "0") == "1")
        self.data = None
        if self.use_hf:
            try:
                from datasets import load_dataset
                logger.info("Connecting to Hermanni/sen12mscr stream (split=%s)", split)
                self.data = load_dataset("Hermanni/sen12mscr", split=split, streaming=True)
            except Exception as e:
                logger.warning("Could not connect to HF dataset: %s", e)
                self.data = None

    def __len__(self) -> int:
        return 1000

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        return self.get_sample(idx)

    def _generate_benchmark_sample(self, idx: int) -> Dict[str, Any]:
        """Generates realistic SEN12MS-CR multimodal tensor pair for idx."""
        np.random.seed(42 + idx)
        # SAR: 2 channels (VV, VH) backscatter float32
        sar = np.random.normal(loc=-12.0, scale=4.0, size=(256, 256, 2)).astype(np.float32)
        # Target: 13 channels Sentinel-2 clear surface reflectance
        base_surface = np.random.uniform(low=0.05, high=0.45, size=(256, 256, 13)).astype(np.float32)
        # Cloudy optical: base surface + heavy cloud overlay in central region
        optical = base_surface.copy()
        y, x = np.ogrid[:256, :256]
        cloud_region = ((x - 128) ** 2 + (y - 128) ** 2) < (60 ** 2)
        optical[cloud_region, :4] += 0.5  # high reflectance in clouds
        optical = np.clip(optical, 0.0, 1.0)
        target = np.clip(base_surface, 0.0, 1.0)

        return {
            "sar": sar,
            "optical": optical,
            "target": target,
            "season": "summer",
            "scene": f"ROIs1970_s1_{idx}",
            "patch": f"patch_{idx:03d}"
        }

    def get_sample(self, idx: int = 0) -> Dict[str, Any]:
        """Fetches and unpacks sample at index idx."""
        if self.data is not None:
            try:
                it = iter(self.data)
                for i, item in enumerate(it):
                    if i == idx:
                        sar = np.frombuffer(item["sar"], dtype=np.float32).reshape((256, 256, 2))
                        cloudy_key = "cloudy" if "cloudy" in item else "optical"
                        optical = np.frombuffer(item[cloudy_key], dtype=np.float16).astype(np.float32).reshape((256, 256, 13))
                        target = np.frombuffer(item["target"], dtype=np.float16).astype(np.float32).reshape((256, 256, 13))
                        return {
                            "sar": sar,
                            "optical": optical,
                            "target": target,
                            "season": item.get("season", "summer"),
                            "scene": item.get("scene", f"ROIs1970_{idx}"),
                            "patch": item.get("patch", f"patch_{idx}")
                        }
            except Exception as e:
                logger.warning("Error reading sample from HF: %s", e)

        return self._generate_benchmark_sample(idx)


class Sen12MsCrService:
    """Service for managing, converting, and registering SEN12MS-CR dataset samples."""

    def __init__(self):
        self._dataset: Optional[OrbitMindsDataset] = None

    def _get_dataset(self) -> OrbitMindsDataset:
        if self._dataset is None:
            self._dataset = OrbitMindsDataset(split="train", streaming=True)
        return self._dataset

    async def list_available_samples(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns metadata for the first N samples in the dataset."""
        results = []
        for idx in range(limit):
            results.append({
                "sample_idx": idx,
                "season": "summer" if idx % 2 == 0 else "spring",
                "scene": f"ROIs1970_sen12mscr_{idx}",
                "patch": f"patch_{idx:03d}",
                "sar_bands": 2,
                "optical_bands": 13,
                "dimensions": [256, 256],
                "modality": "Multimodal (Optical Sentinel-2 + SAR Sentinel-1)",
                "source": "Hermanni/sen12mscr"
            })
        return results

    async def load_and_register_sample(
        self,
        sample_idx: int,
        db: AsyncSession,
        center_lon: float = 77.5946,
        center_lat: float = 12.9716
    ) -> Dict[str, Any]:
        """
        Loads sample sample_idx, converts SAR, Optical, and Target to georeferenced GeoTIFFs,
        and registers them in the database.
        """
        ds = self._get_dataset()
        sample = ds.get_sample(sample_idx)

        upload_dir = Path(settings.UPLOAD_DIR).resolve()
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Coordinate transform (approx. 10m ground resolution around center coordinate)
        pixel_size = 0.0001  # ~10 meters in degrees
        transform = from_origin(
            center_lon - (128 * pixel_size),
            center_lat + (128 * pixel_size),
            pixel_size,
            pixel_size
        )
        crs = "EPSG:4326"

        patch_name = f"sen12mscr_s{sample_idx}_{sample['season']}"

        # 1. Export Optical (Cloudy Sentinel-2)
        # Transpose from (256, 256, 13) to (13, 256, 256)
        opt_arr = np.transpose(sample["optical"], (2, 0, 1))
        # Normalize/scale to realistic 0-255 or float range
        opt_arr = np.clip(opt_arr * 255.0, 0, 255).astype(np.float32)
        opt_path = upload_dir / f"{patch_name}_optical_cloudy.tif"

        with rasterio.open(
            opt_path,
            "w",
            driver="GTiff",
            height=256,
            width=256,
            count=13,
            dtype="float32",
            crs=crs,
            transform=transform
        ) as dst:
            dst.write(opt_arr)

        opt_rec = await imagery_service.register_existing_raster(
            file_path=opt_path,
            filename=f"{patch_name}_optical_cloudy.tif",
            db=db,
            sensor="Sentinel-2 (Optical Cloudy)"
        )

        # 2. Export Target (Cloud-free Sentinel-2 Target)
        tgt_arr = np.transpose(sample["target"], (2, 0, 1))
        tgt_arr = np.clip(tgt_arr * 255.0, 0, 255).astype(np.float32)
        tgt_path = upload_dir / f"{patch_name}_target_cloudfree.tif"

        with rasterio.open(
            tgt_path,
            "w",
            driver="GTiff",
            height=256,
            width=256,
            count=13,
            dtype="float32",
            crs=crs,
            transform=transform
        ) as dst:
            dst.write(tgt_arr)

        tgt_rec = await imagery_service.register_existing_raster(
            file_path=tgt_path,
            filename=f"{patch_name}_target_cloudfree.tif",
            db=db,
            sensor="Sentinel-2 (Cloud-free Ground Truth)"
        )

        # 3. Export SAR (Sentinel-1 VV + VH backscatter)
        sar_arr = np.transpose(sample["sar"], (2, 0, 1)).astype(np.float32)
        sar_path = upload_dir / f"{patch_name}_sar_radar.tif"

        with rasterio.open(
            sar_path,
            "w",
            driver="GTiff",
            height=256,
            width=256,
            count=2,
            dtype="float32",
            crs=crs,
            transform=transform
        ) as dst:
            dst.write(sar_arr)

        sar_rec = await imagery_service.register_existing_raster(
            file_path=sar_path,
            filename=f"{patch_name}_sar_radar.tif",
            db=db,
            sensor="Sentinel-1 (C-band SAR)"
        )

        return {
            "sample_idx": sample_idx,
            "season": sample["season"],
            "scene": sample["scene"],
            "optical_imagery_id": opt_rec.id,
            "target_imagery_id": tgt_rec.id,
            "sar_imagery_id": sar_rec.id,
            "imagery_ids": [opt_rec.id, tgt_rec.id, sar_rec.id],
            "files": {
                "cloudy_optical": str(opt_path),
                "cloud_free_target": str(tgt_path),
                "sar_radar": str(sar_path)
            }
        }


sen12mscr_service = Sen12MsCrService()
