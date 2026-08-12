# 🎓 Academia AI — The World's Most Advanced AI Learning Operating System

An intelligent AI-powered education platform that understands entire university curricula and becomes a student's lifelong AI Professor.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose

### Run with Docker (Recommended)

```bash
docker-compose up -d
```

### Development Setup

**Backend:**
```bash
cd backend
python -m venv venv
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 🧠 Architecture

### Backend (FastAPI + Python)
- **Database**: PostgreSQL (async with SQLAlchemy)
- **Cache**: Redis
- **Vector Store**: Qdrant
- **Knowledge Graph**: Neo4j
- **File Storage**: MinIO
- **Task Queue**: Celery
- **AI**: NVIDIA only

### Frontend (Next.js 15 + React 19)
- **State**: Zustand
- **Styling**: Tailwind CSS + Glassmorphism
- **Animations**: Framer Motion
- **Graphs**: React Flow / Recharts / Mermaid

## 🔧 Configuration

Set the NVIDIA credentials in `backend/.env`:
```
AI_PROVIDER=nvidia
NVIDIA_API_KEY=your-key
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

## 📚 Features

- **AI Tutor** — Interactive teaching, never just answers
- **Auto-Organization** — Files → Subjects → Units → Chapters → Topics
- **Knowledge Graph** — Visualize concept relationships
- **Workflow Maps** — Track learning progress visually
- **Quizzes** — Adaptive MCQs, coding, essays
- **Spaced Repetition** — SM-2 flashcards
- **Voice Tutor** — Speech-to-speech learning
- **Whiteboard** — Real-time collaborative drawing
- **Study Plans** — AI-generated exam schedules
- **Memory System** — Long-term learning memory
- **File Support** — PDF, DOCX, PPTX, XLSX, CSV, images, video, audio, URLs

## 🐳 Docker Services

| Service   | Port  |
|-----------|-------|
| Frontend  | 3000  |
| Backend   | 8000  |
| PostgreSQL| 5432  |
| Redis     | 6379  |
| Neo4j     | 7687  |
| Qdrant    | 6333  |
| MinIO     | 9000  |