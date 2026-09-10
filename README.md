# OrbitMind: AI-Powered Remote Sensing & Geospatial Intelligence Backend

OrbitMind is a production-ready, AI-driven remote sensing backend service that orchestrates satellite imagery processing and geospatial analysis through natural-language queries.

OrbitMind accepts multi-spectral, optical, and Synthetic Aperture Radar (SAR) imagery, interprets complex geospatial queries (such as *"Where did urban expansion occur between 2022 and 2025?"*), selects and executes specialist computer vision and remote sensing models, and generates evidence-first georeferenced artifacts (GeoTIFF change masks, segmentation layers, spatial statistics, and GeoJSON boundaries).

> [!IMPORTANT]
> **Strict Backend Architecture**: OrbitMind is an API-first backend system engineered with FastAPI, GDAL, Rasterio, GeoPandas, Shapely, PyTorch, and PostgreSQL/PostGIS. No frontend or dashboard code is included. Interactive API exploration is available via OpenAPI Swagger (`/docs`) and ReDoc (`/redoc`).

---

## Architecture

```
Client / API Request
        │
        ▼
FastAPI Application (/api/v1)
        │
        ▼
Query Understanding (Rule-based / Extensible LLM)
        │
        ▼
OrbitMind Agent Controller (Orchestrator)
        │
        ├───► Geospatial Processing Engine (GDAL, Rasterio, GeoPandas, Shapely, PyProj)
        │
        └───► Specialist Models (BaseRemoteSensingModel via ModelRegistry)
                ├── VQAModel (Visual Question Answering)
                ├── CaptioningModel (Scene Summarization)
                ├── ChangeDetectionModel (Bitemporal Change Detection)
                ├── SegmentationModel (Land Cover Classification)
                └── OpticalSARModel (Optical + SAR Radar Fusion)
        │
        ▼
Evidence Generator & Spatial Statistics
        │
        ▼
Async Background Worker & Database (PostgreSQL + PostGIS / SQLAlchemy Async)
        │
        ▼
Structured JSON API Response (with "mode": "mock" | "production")
```

---

## Tech Stack

| Domain | Technology |
|---|---|
| **API Framework** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2, Pydantic Settings |
| **Geospatial Processing** | GDAL, Rasterio, GeoPandas, Shapely, PyProj |
| **Machine Learning / AI** | PyTorch, Hugging Face Transformers, Hugging Face Hub, NumPy |
| **Image Processing** | Pillow (PIL), OpenCV |
| **Database & ORM** | PostgreSQL, PostGIS, SQLAlchemy 2.0 (Async), Alembic, asyncpg, aiosqlite |
| **Containerization** | Docker, Docker Compose |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX |

---

## Directory Structure

```
orbitmind/
├── app/
│   ├── main.py                     # FastAPI entrypoint, lifespan, and CORS setup
│   ├── api/
│   │   ├── dependencies.py         # Database session & security dependencies
│   │   └── routes/
│   │       ├── health.py           # Health check endpoint (GET /health)
│   │       ├── imagery.py          # Imagery upload & catalog (POST /api/v1/imagery/upload)
│   │       ├── queries.py          # Query intent classification (POST /api/v1/query)
│   │       ├── analysis.py         # Async analysis dispatch (POST /api/v1/analysis)
│   │       ├── jobs.py             # Job lifecycle tracking (GET /api/v1/jobs/{id})
│   │       └── results.py          # Structured result & artifact download
│   ├── core/
│   │   ├── config.py               # Pydantic BaseSettings (.env configuration)
│   │   ├── logging.py              # Centralized logging configuration
│   │   └── security.py             # Filename sanitization, path traversal checks, file size validation
│   ├── schemas/                    # Pydantic v2 validation and serialization schemas
│   │   ├── query.py
│   │   ├── imagery.py
│   │   ├── analysis.py
│   │   ├── evidence.py
│   │   └── response.py
│   ├── models/                     # SQLAlchemy ORM database models
│   │   ├── database.py             # Async database session manager
│   │   ├── imagery.py              # Imagery table schema
│   │   ├── analysis.py             # AnalysisJob table schema
│   │   └── result.py               # AnalysisResult table schema
│   ├── services/
│   │   ├── query_service.py        # Natural language query classifier
│   │   ├── agent_controller.py     # Central orchestration pipeline
│   │   ├── imagery_service.py      # Upload processing and metadata extraction
│   │   ├── preprocessing_service.py # CRS check, raster alignment, bounding box overlap
│   │   ├── evidence_service.py     # Artifact and provenance compiler
│   │   ├── statistics_service.py   # Spatial statistics calculation
│   │   └── satellite_providers.py  # Local, Sentinel, and Landsat provider interfaces
│   ├── ai/
│   │   ├── base.py                 # BaseRemoteSensingModel abstract interface
│   │   ├── registry.py             # Dynamic model registry
│   │   ├── change_detection.py     # Bi-temporal change detection specialist
│   │   ├── segmentation.py         # Semantic land cover segmentation specialist
│   │   ├── vqa.py                  # Visual Question Answering specialist
│   │   ├── captioning.py           # Scene captioning specialist
│   │   └── optical_sar.py          # Optical + SAR radar multimodal specialist
│   ├── geospatial/
│   │   ├── raster.py               # Rasterio/GDAL GeoTIFF reader/writer/metadata
│   │   ├── vector.py               # Mask polygonization & geodesic area (km²)
│   │   ├── crs.py                  # CRS parsing and equivalence verification
│   │   ├── reprojection.py         # Raster alignment and coordinate reprojection
│   │   └── statistics.py           # Pixel and surface metric calculations
│   └── workers/
│       └── analysis_worker.py      # Background async worker task
├── tests/                          # Complete automated test suite (no GPU required)
│   ├── conftest.py                 # Async fixtures & synthetic GeoTIFF generator
│   ├── test_health.py
│   ├── test_imagery.py
│   ├── test_query.py
│   ├── test_geospatial.py
│   ├── test_models.py
│   └── test_analysis_jobs.py
├── migrations/                     # Alembic database migration scripts
│   ├── env.py
│   └── versions/001_initial_tables.py
├── data/                           # Local storage volumes
│   ├── uploads/
│   ├── processed/
│   └── results/
├── Dockerfile                      # Production Docker container definition
├── docker-compose.yml              # PostGIS and API service orchestration
├── requirements.txt                # Python package dependencies
├── .env.example                    # Environment variable template
├── alembic.ini                     # Alembic configuration
└── pytest.ini                      # Pytest configuration
```

---

## Installation & Setup

### Prerequisites
- Python 3.11+
- GDAL libraries (or use the pre-configured Docker image)

### Local Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Aakarsh1458/orbit_mind.git
   cd orbit_mind
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   *Note: For local testing without a running PostgreSQL instance, set `DATABASE_URL=sqlite+aiosqlite:///./orbitmind.db` in `.env`.*

5. **Run Database Migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start the FastAPI Server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   - OpenAPI documentation will be accessible at: `http://localhost:8000/docs`
   - ReDoc documentation will be accessible at: `http://localhost:8000/redoc`

---

## Docker Setup

OrbitMind includes a multi-container Docker Compose configuration pairing the FastAPI backend with a dedicated PostgreSQL instance equipped with the PostGIS spatial extensions.

### Start with Docker Compose:

```bash
docker compose up --build
```

This starts:
1. `orbitmind-db`: PostgreSQL 16 + PostGIS 3.4 on port `5432`
2. `orbitmind-api`: FastAPI backend on port `8000`

### Verify container health:
```bash
docker compose ps
curl http://localhost:8000/health
```

---

## Mock Mode vs. Production Mode

OrbitMind enforces strict scientific integrity: **AI results are never faked.**

### `AI_MODE=mock` (Default Development Mode)
- Deterministic, mathematically verifiable baseline computations.
- Bitemporal change detection calculates actual pixel differences and exports valid GeoTIFF change masks.
- Responses are explicitly marked: `"mode": "mock"`.
- Runs on any standard CPU without downloading gigabytes of weights.

### `AI_MODE=production` (Production Deep Learning Mode)
- Invokes trained PyTorch / Hugging Face model pipelines.
- Reads deep neural network checkpoints from `MODEL_CACHE_DIR`.
- If model weights or required hardware are unavailable, the backend fails safely with a clear, descriptive exception rather than fabricating confidence scores or masks.

### How to Switch Modes:
Edit `.env` or set the environment variable:
```bash
# To switch to production:
AI_MODE=production

# To switch back to mock:
AI_MODE=mock
```

---

## API Endpoints & Example Usage

### 1. Health Check
```bash
curl -X GET http://localhost:8000/health
```
**Response:**
```json
{
  "status": "ok",
  "service": "orbitmind-backend",
  "version": "1.0.0",
  "ai_mode": "mock"
}
```

---

### 2. Upload Satellite Imagery
Upload a GeoTIFF, TIFF, or PNG/JPEG raster file. The backend automatically parses spatial metadata (CRS, dimensions, bands, bounds, resolution, affine transform).

```bash
curl -X POST http://localhost:8000/api/v1/imagery/upload \
  -F "file=@data/samples/berlin_2022.tif" \
  -F "sensor=Sentinel-2"
```

**Response (`201 Created`):**
```json
{
  "id": "5f4a8da3-1b2c-4d5e-8f9a-0b1c2d3e4f5a",
  "filename": "berlin_2022.tif",
  "path": "/app/data/uploads/109dcc4f_berlin_2022.tif",
  "sensor": "Sentinel-2",
  "crs": "EPSG:4326",
  "width": 1024,
  "height": 1024,
  "bands": 4,
  "bounds": {
    "left": 13.35,
    "bottom": 52.48,
    "right": 13.45,
    "top": 52.55
  },
  "resolution": [0.0001, 0.0001],
  "dtype": "uint16",
  "is_georeferenced": true,
  "file_size_bytes": 8388608,
  "created_at": "2026-09-10T06:30:00Z"
}
```

---

### 3. Natural Language Query Understanding
Test how the query classifier interprets your natural-language request before queuing analysis.

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Where did urban expansion occur between 2022 and 2025?",
    "imagery_ids": [
      "5f4a8da3-1b2c-4d5e-8f9a-0b1c2d3e4f5a",
      "73ea25fa-2c3d-4e5f-9a0b-1c2d3e4f5a6b"
    ]
  }'
```

**Response (`200 OK`):**
```json
{
  "query_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "query": "Where did urban expansion occur between 2022 and 2025?",
  "detected_intent": "change_detection",
  "confidence": 0.91,
  "reason": "The query asks for temporal differences or surface evolution.",
  "selected_analysis": "change_detection",
  "status": "ready"
}
```

---

### 4. Start an Asynchronous Analysis Job
Launches the analysis asynchronously without blocking the client. Returns immediately with `job_id` and `queued` status.

```bash
curl -X POST http://localhost:8000/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Where did urban expansion occur between 2022 and 2025?",
    "imagery_ids": [
      "5f4a8da3-1b2c-4d5e-8f9a-0b1c2d3e4f5a",
      "73ea25fa-2c3d-4e5f-9a0b-1c2d3e4f5a6b"
    ]
  }'
```

**Response (`202 Accepted`):**
```json
{
  "job_id": "edd02685-9931-4155-91d0-340f3f7375d1",
  "status": "queued",
  "analysis_type": "change_detection",
  "created_at": "2026-09-10T06:35:00Z"
}
```

---

### 5. Check Job Status
Poll or monitor job execution progress.

```bash
curl -X GET http://localhost:8000/api/v1/jobs/edd02685-9931-4155-91d0-340f3f7375d1
```

**Response (`200 OK`):**
```json
{
  "job_id": "edd02685-9931-4155-91d0-340f3f7375d1",
  "query": "Where did urban expansion occur between 2022 and 2025?",
  "analysis_type": "change_detection",
  "status": "completed",
  "progress": 1.0,
  "created_at": "2026-09-10T06:35:00Z",
  "started_at": "2026-09-10T06:35:01Z",
  "completed_at": "2026-09-10T06:35:04Z",
  "error": null
}
```

---

### 6. Retrieve Structured Analysis Results
Fetch full structured results, including summary, model confidence, calculated area ($km^2$), evidence links, and execution provenance trace.

```bash
curl -X GET http://localhost:8000/api/v1/results/edd02685-9931-4155-91d0-340f3f7375d1
```

**Response (`200 OK`):**
```json
{
  "job_id": "edd02685-9931-4155-91d0-340f3f7375d1",
  "analysis_type": "change_detection",
  "mode": "mock",
  "summary": "Bitemporal change detection identified 12.40 km² (14.06%) of surface changes between the specified acquisition periods.",
  "confidence": 0.88,
  "statistics": {
    "total_pixels": 409600,
    "changed_pixels": 57600,
    "unchanged_pixels": 352000,
    "percentage_changed": 14.06,
    "changed_area_km2": 12.4,
    "total_area_km2": 88.2,
    "changed_area_hectares": 1240.0
  },
  "evidence": {
    "change_mask": "/data/results/change_mask_5f4a8da3_berlin_2022_73ea25fa_berlin_2025.tif",
    "source_images": [
      "/data/uploads/5f4a8da3_berlin_2022.tif",
      "/data/uploads/73ea25fa_berlin_2025.tif"
    ],
    "crs": "EPSG:4326",
    "detected_regions_count": 14,
    "sample_footprints": [
      {
        "type": "Polygon",
        "coordinates": [[[13.407, 52.518], [13.407, 52.515], [13.409, 52.515], [13.409, 52.518], [13.407, 52.518]]]
      }
    ]
  },
  "execution_trace": [
    "query_understanding",
    "imagery_validation",
    "geospatial_preprocessing",
    "change_detection",
    "statistics",
    "evidence_generation"
  ],
  "created_at": "2026-09-10T06:35:04Z"
}
```

---

### 7. Download Generated Evidence Mask (GeoTIFF)
Directly download the georeferenced output GeoTIFF file for visualization in GIS software (QGIS, ArcGIS, GDAL CLI):

```bash
curl -X GET "http://localhost:8000/api/v1/results/edd02685-9931-4155-91d0-340f3f7375d1/download/change_mask_5f4a8da3_berlin_2022_73ea25fa_berlin_2025.tif" \
  --output change_mask.tif
```

---

## Automated Testing

Run the full test suite without needing a GPU:

```bash
pytest -v
```

### What is tested:
- `test_health.py`: Health endpoint status and service information.
- `test_imagery.py`: GeoTIFF upload, spatial metadata extraction (bounds, resolution, CRS, transform), and security validation (path traversal, invalid extensions).
- `test_query.py`: Intent classification across all 5 specialist tasks (VQA, captioning, change detection, segmentation, optical/SAR).
- `test_geospatial.py`: Raster reading, writing, CRS conversion, spatial overlap checks, mask polygonization, and geodesic area ($km^2$) calculations.
- `test_models.py`: Specialist model interfaces, registry lookup, mock execution, and production mode safety checks.
- `test_analysis_jobs.py`: Complete end-to-end integration workflow (uploading T1/T2 synthetic GeoTIFFs, queuing analysis, executing worker, verifying structured results, and downloading evidence).

---

## Satellite Data Integration

OrbitMind includes the `SatelliteDataProvider` abstraction (`app/services/satellite_providers.py`) designed for extensible remote sensing catalog integration:

- **`LocalFileProvider`**: Currently active for user-uploaded rasters and local scenes.
- **`SentinelProvider`**: Plug-and-play stub for European Space Agency Copernicus STAC APIs (Sentinel-1 SAR and Sentinel-2 Multi-Spectral).
- **`LandsatProvider`**: Plug-and-play stub for USGS Landsat 8/9 STAC catalogs.

To connect external STAC catalogs, configure API credentials in `.env` and initialize the corresponding provider in `app/services/satellite_providers.py`.
