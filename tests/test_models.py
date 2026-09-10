from pathlib import Path
import pytest
from app.ai.registry import model_registry
from app.ai.change_detection import ChangeDetectionModel
from app.ai.segmentation import SegmentationModel
from app.ai.vqa import VQAModel
from app.ai.captioning import CaptioningModel
from app.ai.optical_sar import OpticalSARModel


def test_model_registry():
    """Verify model registry returns all 5 specialist models."""
    available = model_registry.list_available_models()
    expected = {"vqa", "captioning", "change_detection", "segmentation", "optical_sar"}
    assert expected.issubset(set(available.keys()))

    cd_model = model_registry.get_model("change_detection", mode="mock")
    assert isinstance(cd_model, ChangeDetectionModel)
    assert cd_model.mode == "mock"

    with pytest.raises(KeyError):
        model_registry.get_model("unsupported_task")


def test_change_detection_mock(sample_geotiff_t1: str, sample_geotiff_t2: str, tmp_path: Path):
    """Test ChangeDetectionModel execution in mock mode."""
    model = ChangeDetectionModel(mode="mock")
    model.load()

    output = model.predict({
        "imagery_paths": [sample_geotiff_t1, sample_geotiff_t2],
        "output_dir": str(tmp_path)
    })

    assert output["mode"] == "mock"
    assert "summary" in output
    assert output["confidence"] > 0.8
    assert "statistics" in output
    assert output["statistics"]["changed_pixels"] > 0
    assert "evidence" in output
    assert Path(output["evidence"]["change_mask"]).exists()


def test_segmentation_mock(sample_geotiff_t1: str, tmp_path: Path):
    """Test SegmentationModel execution in mock mode."""
    model = SegmentationModel(mode="mock")
    model.load()

    output = model.predict({
        "imagery_paths": [sample_geotiff_t1],
        "output_dir": str(tmp_path)
    })

    assert output["mode"] == "mock"
    assert output["confidence"] > 0.8
    assert "classes" in output["statistics"]
    assert Path(output["evidence"]["segmentation_mask"]).exists()


def test_vqa_mock(sample_geotiff_t1: str):
    """Test VQAModel execution in mock mode."""
    model = VQAModel(mode="mock")
    model.load()

    output = model.predict({
        "query": "Where is the water visible?",
        "imagery_paths": [sample_geotiff_t1]
    })

    assert output["mode"] == "mock"
    assert "water" in output["summary"].lower()
    assert output["confidence"] > 0.8


def test_captioning_mock(sample_geotiff_t1: str):
    """Test CaptioningModel execution in mock mode."""
    model = CaptioningModel(mode="mock")
    model.load()

    output = model.predict({
        "imagery_paths": [sample_geotiff_t1]
    })

    assert output["mode"] == "mock"
    assert len(output["summary"]) > 20


def test_optical_sar_mock(sample_geotiff_t1: str, sample_geotiff_t2: str, tmp_path: Path):
    """Test OpticalSARModel execution in mock mode."""
    model = OpticalSARModel(mode="mock")
    model.load()

    output = model.predict({
        "imagery_paths": [sample_geotiff_t1, sample_geotiff_t2],
        "output_dir": str(tmp_path)
    })

    assert output["mode"] == "mock"
    assert "evidence" in output
    assert Path(output["evidence"]["fused_raster"]).exists()


def test_production_mode_fails_safely_when_unconfigured(sample_geotiff_t1: str):
    """Verify that in production mode, missing weights raise actionable errors rather than faking results."""
    model = ChangeDetectionModel(mode="production")
    model.load()

    with pytest.raises(NotImplementedError) as exc_info:
        model.predict({
            "imagery_paths": [sample_geotiff_t1, sample_geotiff_t1]
        })
    assert "AI_MODE=mock" in str(exc_info.value)
