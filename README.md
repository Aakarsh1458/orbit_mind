# OrbitMind: AI-Powered Remote Sensing & Geospatial Intelligence Backend

OrbitMind is a production-ready, AI-driven remote sensing backend service that orchestrates satellite imagery processing and geospatial analysis through natural-language queries.

OrbitMind accepts multi-spectral, optical, and Synthetic Aperture Radar (SAR) imagery, interprets complex geospatial queries (such as *"Where did urban expansion occur between 2022 and 2025?"*), selects and executes specialist computer vision and remote sensing models, and generates evidence-first georeferenced artifacts (GeoTIFF change masks, segmentation layers, spatial statistics, and GeoJSON boundaries).

> [!IMPORTANT]
> **Strict Backend Architecture**: OrbitMind is an API-first backend system engineered with FastAPI, GDAL, Rasterio, GeoPandas, Shapely, PyTorch, and PostgreSQL/PostGIS. No frontend or dashboard code is included. Interactive API exploration is available via OpenAPI Swagger (`/docs`) and ReDoc (`/redoc`).

---

## Architecture & AI Orchestration Flow

```
                           NATURAL LANGUAGE USER QUERY
                                       │
                                       ▼
                  POST /api/v1/chat    │   POST /api/v1/chat/stream
                                       │
                                       ▼
                             OrbitMindOrchestrator
                             (OrchestrationState)
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
    QueryUnderstanding            TaskPlanner            ConversationMemory
   (Structured Pydantic)      (Detects missing inputs)  (Multi-turn Sessions)
            │                          │                          │
            └──────────────────────────┼──────────────────────────┘
                                       │
                                       ▼
                            ModelRouter & LLMRouter
                         (Primary & Fallback Selection)
                                       │
                                       ▼
                                  ToolEngine
                      (ToolRegistry & Geospatial Tools)
                                       │
                                       ▼
                            Specialist Model Engine
                       (VQA, Change Detection, Seg, SAR)
                                       │
                                       ▼
                               OutputValidator
                     (CRS, Dtype, Bounds, Mask, Overlap)
                                       │
                          [If Invalid or Model Fails]
                                       ▼
                             RetryEngine & Policies
                         (Exponential Backoff & Fallback)
                                       │
                                       ▼
                                EvidenceEngine
                       (GeoTIFF masks, GeoJSON, Stats)
                                       │
                                       ▼
                               ResponseGenerator
                       (Strictly Factual Natural Answer)
                                       │
                                       ▼
                           Database Persistence &
                           Structured JSON Response
```

---

## Tech Stack

| Domain | Technology |
|---|---|
| **API Framework** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2, Pydantic Settings |
| **LLM Orchestration** | Provider Abstraction (Google Gemini, OpenAI, Hugging Face, Local LLMs) |
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
│   ├── main.py                     # FastAPI entrypoint, lifespan, CORS, and router registration
│   ├── api/
│   │   ├── dependencies.py         # Database session & security dependencies
│   │   └── routes/
│   │       ├── health.py           # Health check endpoint (GET /health)
│   │       ├── chat.py             # Sync & SSE chat API (POST /api/v1/chat, /stream)
│   │       ├── conversations.py    # Multi-turn conversation sessions (CRUD & messages)
│   │       ├── ai_status.py        # Subsystem status, models, and provider health
│   │       ├── imagery.py          # Imagery upload & catalog (POST /api/v1/imagery/upload)
│   │       ├── queries.py          # Query intent classification (POST /api/v1/query)
│   │       ├── analysis.py         # Async analysis dispatch (POST /api/v1/analysis)
│   │       ├── jobs.py             # Job lifecycle tracking (GET /api/v1/jobs/{id})
│   │       └── results.py          # Structured result & artifact download
│   ├── core/
│   │   ├── config.py               # Pydantic BaseSettings (.env configuration)
│   │   ├── logging.py              # Centralized structured logging configuration
│   │   └── security.py             # Filename sanitization, path traversal checks
│   ├── orchestration/              # Core AI Orchestration Subsystem
│   │   ├── orchestrator.py         # OrbitMindOrchestrator bounded execution engine
│   │   ├── state.py                # OrchestrationState typed lifecycle object
│   │   ├── planner.py              # TaskPlanner & StructuredIntent verification
│   │   ├── router.py               # ModelRouter with fallback lookup
│   │   ├── executor.py             # ExecutionEngine for tools & models
│   │   ├── validator.py            # OutputValidator (CRS, schema, mask, NaN, overlap)
│   │   ├── retry_engine.py         # RetryEngine with exponential backoff & fallback
│   │   ├── response_generator.py   # Grounded natural language synthesizer
│   │   └── policies.py             # RetryPolicy, FallbackPolicy, and SafetyPolicy
│   ├── llm/                        # Decoupled LLM Vendor Abstraction
│   │   ├── base.py                 # BaseLLMProvider abstract interface
│   │   ├── gemini_provider.py      # Google Gemini REST client
│   │   ├── openai_provider.py      # OpenAI-compatible API client
│   │   ├── huggingface_provider.py # Hugging Face Inference client
│   │   ├── local_provider.py       # Local model client (Ollama / vLLM)
│   │   └── router.py               # LLMRouter with provider failover
│   ├── tools/                      # Tool Registry & Security
│   │   ├── registry.py             # ToolRegistry with whitelisted geospatial tools
│   │   └── schema.py               # ToolCall & argument validation schemas
│   ├── ai/                         # Specialist Remote Sensing AI Models
│   │   ├── base.py                 # BaseRemoteSensingModel & ModelCapability
│   │   ├── registry.py             # ModelRegistry with primary & fallback models
│   │   ├── change_detection.py     # Bi-temporal change detector & fallback
│   │   ├── segmentation.py         # Multi-class land cover segmentation
│   │   ├── vqa.py                  # Visual Question Answering
│   │   ├── captioning.py           # Scene captioning specialist
│   │   └── optical_sar.py          # Optical + SAR radar multimodal specialist
│   ├── geospatial/                 # Spatial math & raster operations
│   │   ├── raster.py               # GeoTIFF reading, writing, windowing, and tags
│   │   ├── vector.py               # Mask polygonization & geodesic area (km²)
│   │   ├── crs.py                  # Coordinate reference system parsing & equivalence
│   │   ├── reprojection.py         # Raster alignment and coordinate reprojection
│   │   └── statistics.py           # Changed surface and class metric calculations
│   ├── models/                     # SQLAlchemy ORM Database Schemas
│   │   ├── database.py             # Async engine & session factory
│   │   ├── imagery.py              # Imagery table schema
│   │   ├── analysis.py             # AnalysisJob table schema
│   │   ├── result.py               # AnalysisResult table schema
│   │   └── conversation.py         # Conversations, messages, and orchestration runs
│   ├── services/                   # Business domain services
│   │   ├── conversation_service.py # Multi-turn memory management
│   │   ├── imagery_service.py      # Upload and metadata extraction
│   │   └── satellite_providers.py  # Local, Sentinel, and Landsat providers
│   └── workers/
│       └── analysis_worker.py      # Background async worker task
├── tests/                          # Automated Pytest Suite (30 tests, 0 warnings)
│   ├── conftest.py                 # Synthetic GeoTIFF generator & async fixtures
│   ├── test_health.py
│   ├── test_ai_status.py
│   ├── test_chat_api.py
│   ├── test_conversations.py
│   ├── test_orchestration_loop.py
│   ├── test_orchestration_failure.py
│   ├── test_orchestration_validation.py
│   ├── test_orchestration_missing_inputs.py
│   ├── test_imagery.py
│   ├── test_query.py
│   ├── test_geospatial.py
│   ├── test_models.py
│   └── test_analysis_jobs.py
├── migrations/                     # Alembic database migrations
│   ├── versions/
│   │   ├── 001_initial_tables.py
│   │   └── 002_orchestration_tables.py
├── data/                           # Local storage volumes (uploads, processed, results)
├── Dockerfile                      # Production Docker container
├── docker-compose.yml              # PostGIS and API service orchestration
├── requirements.txt
├── .env.example
├── alembic.ini
└── pytest.ini
```

---

## Installation & Setup

### Prerequisites
- Python 3.11+
- GDAL libraries (included automatically in Docker or pre-installed in environment)

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
   *Note: For local development on bare metal without Docker, the backend automatically uses `sqlite+aiosqlite:///./data/orbitmind.db` if no external PostgreSQL server is detected.*

5. **Start the FastAPI Server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   - OpenAPI documentation will be accessible at: `http://localhost:8000/docs`
   - ReDoc documentation will be accessible at: `http://localhost:8000/redoc`

---

## Docker Setup

OrbitMind includes a multi-container Docker Compose configuration pairing the FastAPI backend with a dedicated PostgreSQL instance equipped with the PostGIS spatial extensions.

```bash
docker compose up --build
```

This spins up:
1. `orbitmind-db`: PostgreSQL 16 + PostGIS 3.4 on port `5432`
2. `orbitmind-api`: FastAPI backend on port `8000`

---

## Where to Provide API Keys and Model IDs

OrbitMind enforces strict security: **API keys are NEVER hardcoded, committed to git, or printed in logs.**

Configure your credentials in `.env` (or environment variables in Docker):

```ini
# Choose default LLM provider: gemini, openai, huggingface, or local
DEFAULT_LLM_PROVIDER=gemini

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# Hugging Face API
HF_TOKEN=your_hf_token_here
HF_MODEL_ID=meta-llama/Llama-3.1-8B-Instruct

# Local LLM (Ollama / vLLM / LocalAI)
LOCAL_LLM_URL=http://localhost:11434/v1
```

---

## Mock Mode vs. Production Mode

OrbitMind enforces strict scientific integrity: **AI results are never faked.**

### `AI_MODE=mock` (Default Development Mode)
- Follows the identical full orchestration pipeline: `query -> planner -> router -> tools -> model -> validator -> evidence -> response`.
- Bitemporal change detection calculates actual pixel differences and exports valid GeoTIFF change masks.
- Responses are explicitly marked: `"mode": "mock"`.
- Runs on any standard CPU without downloading gigabytes of weights.

### `AI_MODE=production` (Production Deep Learning Mode)
- Invokes trained PyTorch / Hugging Face model pipelines.
- Reads deep neural network checkpoints from `MODEL_CACHE_DIR`.
- If model weights or required hardware are unavailable, the backend fails safely with a clear, descriptive exception (`MODEL_UNAVAILABLE`) rather than fabricating confidence scores or masks.

---

## API Endpoints & Example Usage

### 1. Synchronous Chat API (`POST /api/v1/chat`)

Send natural language queries to trigger complete AI orchestration:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Where did urban expansion occur between 2022 and 2025?",
    "imagery_ids": [
      "5f4a8da3-1b2c-4d5e-8f9a-0b1c2d3e4f5a",
      "73ea25fa-2c3d-4e5f-9a0b-1c2d3e4f5a6b"
    ]
  }'
```

**Response (`200 OK`):**
```json
{
  "request_id": "3289e753-bd7c-4e68-a1f6-399657a23fd7",
  "conversation_id": "329ef672-980c-4e19-a3c2-2a5ffe264b19",
  "status": "completed",
  "answer": "Bitemporal change detection identified 1.24 km² (25.0%) of urban expansion between 2022 and 2025.",
  "analysis": {
    "task": "change_detection",
    "model": "OrbitMind-BiTemporal-ChangeDetector-v1",
    "fallback_used": false,
    "provider": "mock"
  },
  "statistics": {
    "total_pixels": 400,
    "changed_pixels": 100,
    "unchanged_pixels": 300,
    "percentage_changed": 25.0,
    "changed_area_km2": 1.2392,
    "total_area_km2": 4.9569,
    "changed_area_hectares": 123.92
  },
  "evidence": [
    {
      "type": "change_mask",
      "path": "/data/results/change_mask_scene1_scene2.tif"
    },
    {
      "type": "source_images",
      "paths": ["/data/uploads/scene1.tif", "/data/uploads/scene2.tif"]
    },
    {
      "type": "crs",
      "path": "EPSG:4326"
    }
  ],
  "execution": {
    "steps": 8,
    "duration_ms": 108.06,
    "trace": [
      "query_understanding",
      "planning",
      "model_selection",
      "preprocessing",
      "inference",
      "validation",
      "evidence_generation",
      "response_generation"
    ]
  },
  "errors": null
}
```

---

### 2. Streaming Chat API with Server-Sent Events (`POST /api/v1/chat/stream`)

Stream real-time execution progress to clients without exposing private chain-of-thought:

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Where did urban expansion occur between 2022 and 2025?",
    "imagery_ids": ["img1", "img2"]
  }'
```

**Stream Output:**
```
event: status
data: {"stage": "planning"}

event: status
data: {"stage": "model_selection"}

event: status
data: {"stage": "preprocessing"}

event: status
data: {"stage": "inference"}

event: status
data: {"stage": "validation"}

event: completed
data: {"status": "completed", "answer": "...", "analysis": {...}}
```

---

### 3. Missing Input Handling

If a user requests bitemporal change detection but provides only 1 imagery scene:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Where did urban expansion occur between 2022 and 2025?",
    "imagery_ids": ["img_2025_only"]
  }'
```

**Response (`status: needs_input`):**
```json
{
  "request_id": "...",
  "status": "needs_input",
  "answer": "Change detection requires 2 temporal satellite images (before & after), but only 1 was provided. Please provide the required second image.",
  "analysis": {
    "task": "change_detection"
  },
  "execution": {
    "steps": 2,
    "trace": ["query_understanding", "planning"]
  }
}
```

---

### 4. Subsystem Status & Model Capabilities

```bash
# High level system readiness
curl -X GET http://localhost:8000/api/v1/ai/status

# Registered models & capabilities
curl -X GET http://localhost:8000/api/v1/ai/models

# Supported LLM providers
curl -X GET http://localhost:8000/api/v1/ai/providers

# Validate specific provider configuration safely
curl -X POST http://localhost:8000/api/v1/ai/providers/gemini/validate
```

---

### 5. Multi-Turn Conversations

```bash
# Create conversation session
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "Urban Expansion Session"}'

# Append message
curl -X POST http://localhost:8000/api/v1/conversations/{id}/messages \
  -H "Content-Type: application/json" \
  -d '{"role": "user", "content": "Analyze this region."}'

# Get message history
curl -X GET http://localhost:8000/api/v1/conversations/{id}/messages
```

---

## Automated Testing

Run the full test suite (30 unit & integration tests, no GPU required):

```bash
pytest -v
```

### Verified Test Cases:
- `test_orchestration_loop.py`: Primary model failure -> Retry engine catches error -> Invokes fallback model -> Successful inference -> Validation -> Response.
- `test_orchestration_failure.py`: All models fail -> Halts after `MAX_RETRIES` with `AI_EXECUTION_FAILED` without entering an infinite loop.
- `test_orchestration_validation.py`: Detects and rejects invalid model output (NaN confidence, missing masks, corrupted dictionaries).
- `test_orchestration_missing_inputs.py`: Temporal query with 1 image halts safely with `needs_input`.
- `test_chat_api.py`: Sync (`POST /api/v1/chat`) and streaming (`POST /api/v1/chat/stream`) SSE verification.
- `test_conversations.py`: Multi-turn session creation, message logging, and context retention.
- `test_ai_status.py`: Health, model capabilities, and safe provider credential validation.
- `test_health.py`, `test_imagery.py`, `test_query.py`, `test_geospatial.py`, `test_models.py`, `test_analysis_jobs.py`.
