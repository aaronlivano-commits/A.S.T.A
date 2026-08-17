# System Architecture & Documentation: A.S.T.A. (Augmented Student Technological Assistance)

## 1. Overview & Vision
**A.S.T.A. (Augmented Student Technological Assistance)** is an advanced, AI-powered educational ecosystem engineered to serve as an intelligent tutor, study manager, and multimodal learning companion for students.

A.S.T.A. transforms traditional passive studying into an interactive, grounded, and visual learning process by utilizing cutting-edge Large Multimodal Models (LMMs), vector-based Retrieval-Augmented Generation (RAG), computer vision, and modern web tech stacks.

---

## 2. Core Features & Capabilities

### 2.1 Multimodal Document Scanning & Parsing
- **Document Processing**: Supports PDFs, handwritten notes, lecture slides, and images.
- **Smart Chunking & Vectorization**: Converts study materials into semantic vector embeddings for rapid contextual retrieval.

### 2.2 Google Lens-Style Visual Inquiry
- **Interactive Region-of-Interest (ROI) Cropping**: Allows students to select mathematical equations, biological diagrams, or physics problems from camera feeds or uploaded images.
- **Visual Reasoning**: Analyzes figures and handwriting directly using Gemini Vision models to provide step-by-step solutions and explanations.

### 2.3 Grounded Interactive Chatbot
- **Material-Anchored Answers**: Responds strictly based on the student's uploaded study materials to eliminate hallucinations.
- **Real-Time Token Streaming**: Provides low-latency chat interaction using Server-Sent Events (SSE) / WebSockets.

### 2.4 Personal Data Training & Model Export/Import (Zero-Retraining Sharing)
- **Text-Based Training Input**: Supports raw training datasets via **`.csv`**, **`.json`**, and **`.xlsx`** files containing QA pairs, terminology tables, or custom study profiles.
- **Vision-Based Training Input**: Accepts image archives (**`.zip`** containing labeled images) for custom visual recognition fine-tuning and object/diagram classification.
- **Model Export**: Packages trained adapters (`.safetensors` / LoRA), prompt personas, and vectorized knowledge graphs into a self-contained **`.asta-model`** bundle.
- **Zero-Retraining Import**: Allows other users to import `.asta-model` packages directly into their local or cloud A.S.T.A. instance, enabling immediate usage of customized AI models without re-running data training processes.

### 2.5 Cloud Sync & Portability
- **Firebase Infrastructure**: Authenticates via Google Identity (Firebase Auth), syncs topic state using Cloud Firestore, and retains files in Firebase Storage.
- **Complete Data Portability**: Enables full offline and cloud backup/restore of topic contexts, chat logs, and vector stores via `.asta` / `.json` / `.zip` archives.

---

## 3. Tech Stack Architecture

### Frontend (User Interface)
- **Framework & Build**: Vite + React
- **Styling & UI Components**: Tailwind CSS, Radix UI Primitives, shadcn/ui
- **Micro-Animations**: GSAP (GreenSock Animation Platform) for HUD scanning reticles, typewriter reveals, and smooth transitions
- **Client SDKs**: Firebase Web SDK (`auth`, `firestore`, `storage`)

### Backend (AI Engine & Processing)
- **Framework**: Python (FastAPI)
- **AI Core Engine**: Google Gemini API (**Gemini 3.7 Flash** / **Gemini 3.6 Flash**) via `@google/genai`
- **Data Training Engine**:
  - `pandas` / `openpyxl` for CSV/JSON/XLSX text dataset parsing and structured dataset formatting.
  - `Pillow` / `PyTorch` / `PEFT` (Parameter-Efficient Fine-Tuning) for processing custom image datasets and generating lightweight LoRA adapters.
- **OCR & Computer Vision Engine**: OpenCV, EasyOCR, Pillow
- **Vector Database**: ChromaDB / FAISS with `text-embedding-004`
- **Auth Guard**: Firebase Admin SDK (JWT Validation)

---

## 4. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|               A.S.T.A. FRONTEND (Vite + React + Tailwind + GSAP)                  |
|  +-----------------------+   +-----------------------+   +---------------------+  |
|  | shadcn/Radix UI Core  |   | Training & Model UI   |   | Firebase SDK Client |  |
|  | (Dashboard, Chat, ROI)|   | (Dataset Import/Export|   | (Auth, Firestore)   |  |
|  +-----------+-----------+   +-----------+-----------+   +----------+----------+  |
+--------------|---------------------------|--------------------------|-------------+
               | REST / WebSockets / SSE   |                          |
               v                           v                          v
+--------------------------------------+ +------------------------------------------+
|     A.S.T.A. BACKEND (FastAPI)       | |        GOOGLE & FIREBASE SERVICES        |
|  +--------------------------------+  | |  +-------------------+ +---------------+ |
|  | REST API Router & Auth Guard   |  | |  | Gemini AI Engine  | | Firebase Auth | |
|  | (Firebase Admin SDK / JWT)     |  | |  | (3.7 / 3.6 Flash)   | | (Google Auth) | |
|  +---------------+----------------+  | |  +-------------------+ +---------------+ |
|                  |                   | |  +-------------------+ +---------------+ |
|                  v                   | |  | Cloud Firestore   | | Cloud Storage | |
|  +--------------------------------+  | |  | (Topic Data Sync) | | (Raw Assets)  | |
|  | Vision, OCR, RAG & Training    |  | |  +-------------------+ +---------------+ |
|  | (ChromaDB, Pandas, PEFT/LoRA)    |  | +------------------------------------------+
|  +--------------------------------+  |
+--------------------------------------+
```

---

## 5. Directory Structure Reference

```
asta-ai-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI Entrypoint
│   │   ├── config.py
│   │   ├── firebase_config.py      # Admin SDK Configuration
│   │   ├── routers/
│   │   │   ├── documents.py
│   │   │   ├── vision.py
│   │   │   ├── chat.py
│   │   │   ├── training.py          # Dataset ingestion (CSV, JSON, XLSX, Images)
│   │   │   └── portability.py       # .asta-model export/import engine
│   │   └── services/
│   │       ├── gemini_engine.py    # Gemini 3.7 Flash Integration
│   │       ├── dataset_trainer.py  # Data parsing & LoRA adapter builder
│   │       ├── vector_store.py
│   │       └── model_exporter.py   # Packager for pre-trained AI sharing
│   └── requirements.txt
└── frontend/                        # Vite + React Client
    ├── vite.config.js
    ├── tailwind.config.js
    ├── components.json              # shadcn/ui config
    ├── src/
    │   ├── main.jsx
    │   ├── App.jsx
    │   ├── firebase/
    │   │   └── config.js            # Client-side Firebase SDK init
    │   ├── components/
    │   │   ├── ui/                  # shadcn/ui components
    │   │   ├── Dashboard.jsx
    │   │   ├── LensScanner.jsx      # Google Lens ROI UI + GSAP FX
    │   │   ├── ChatWindow.jsx       # Gemini Stream + GSAP Typewriter
    │   │   ├── ModelTrainerModal.jsx# Data Training UI (CSV/JSON/XLSX & Images)
    │   │   └── TopicManager.jsx
    │   ├── animations/
    │   │   ├── gsapHooks.js         # GSAP Custom Hooks
    │   │   └── scanEffects.js       # GSAP HUD Reticle FX
    │   └── styles/
    │       └── globals.css
```

---

## 6. API Endpoint Summary

| Endpoint | Method | Auth Required | Description |
|---|---|---|---|
| `/api/v1/auth/verify` | `POST` | Yes (Firebase) | Verifies JWT Token and initializes user profile |
| `/api/v1/topics` | `GET / POST` | Yes (Firebase) | Manages student study topics |
| `/api/v1/documents/upload` | `POST` | Yes (Firebase) | Uploads PDF/images for OCR and vector embedding |
| `/api/v1/training/text` | `POST` | Yes (Firebase) | Uploads text training datasets (`.csv`, `.json`, `.xlsx`) |
| `/api/v1/training/vision` | `POST` | Yes (Firebase) | Uploads vision dataset archive (`.zip` with labeled images) |
| `/api/v1/vision/crop-analyze` | `POST` | Yes (Firebase) | Lens-style ROI image visual analysis via Gemini |
| `/api/v1/chat/stream` | `POST` | Yes (Firebase) | RAG-grounded SSE chat stream using Gemini |
| `/api/v1/models/export/{model_id}` | `GET` | Yes (Firebase) | Exports pre-trained AI model & knowledge bundle (`.asta-model`) |
| `/api/v1/models/import` | `POST` | Yes (Firebase) | Imports `.asta-model` bundle for zero-retraining model sharing |
| `/api/v1/export/{topic_id}` | `GET` | Yes (Firebase) | Exports topic data package (`.asta` ZIP / Cloud) |
| `/api/v1/import` | `POST` | Yes (Firebase) | Imports previously exported `.asta` topic backup |
