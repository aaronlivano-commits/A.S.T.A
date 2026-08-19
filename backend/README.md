# A.S.T.A. Backend

FastAPI service that powers the **Augmented Student Technological Assistance** platform.

## Stack

- **FastAPI** + Uvicorn
- **Google Gemini** (`google-genai`) — text, vision, embeddings
- **ChromaDB** — per-topic vector collections for RAG
- **Firebase Admin** — JWT auth + Firestore topic store
- **pandas / openpyxl** — text dataset parsing
- **EasyOCR / OpenCV / Pillow** — image OCR
- **PEFT / safetensors** — LoRA adapter training (stub)

## Setup

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Fill in GOOGLE_API_KEY and Firebase credentials
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

OpenAPI docs: <http://localhost:8000/docs>

## Directory layout

```
backend/
├── app/
│   ├── main.py                # FastAPI app + lifespan
│   ├── config.py              # Pydantic settings (.env)
│   ├── firebase_config.py     # Admin SDK init
│   ├── dependencies.py        # Auth guard dependency
│   ├── schemas.py             # Pydantic request/response models
│   ├── routers/
│   │   ├── auth.py            # POST /auth/verify
│   │   ├── topics.py          # GET/POST/PATCH/DELETE /topics
│   │   ├── documents.py       # POST /documents/upload
│   │   ├── vision.py          # POST /vision/crop-analyze
│   │   ├── chat.py            # POST /chat/stream (SSE)
│   │   ├── training.py        # POST /training/{text,vision}
│   │   └── portability.py     # /models/export|import, /export|import
│   └── services/
│       ├── gemini_engine.py
│       ├── vector_store.py
│       ├── dataset_trainer.py
│       └── model_exporter.py
├── requirements.txt
├── .env.example
└── .gitignore
```

See `ASTA_AI_System_Architecture.md` (root) for the full system spec.
