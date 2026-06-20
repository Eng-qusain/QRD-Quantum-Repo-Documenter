# RepoDoc Pro — Developer Guide

## Architecture Overview

RepoDoc Pro follows **Clean Architecture** with **Domain-Driven Design (DDD)**. The system has three major layers:

```
┌─────────────────────────────────────────────────────────┐
│                     Electron (Frontend)                   │
│   React + TypeScript + MUI + Redux Toolkit               │
│   IPC bridge via contextBridge (secure)                  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / WebSocket
                         │ localhost:8765
┌────────────────────────▼────────────────────────────────┐
│                  FastAPI Backend (Python)                 │
│   API Routes → Use Cases → Domain → Infrastructure      │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │   Scanner   │  │   Exporter   │  │  AI Documenter │ │
│  │   Service   │  │ Orchestrator │  │  (Claude/GPT)  │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Infrastructure Layer                 │   │
│  │  PDF Builder │ Parsers │ Petroleum │ Storage      │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

## Project Structure

```
repodoc-pro/
├── electron/                    # Desktop app (Electron + React)
│   ├── src/
│   │   ├── main/               # Electron main process
│   │   │   └── main.ts         # App lifecycle, IPC, backend management
│   │   ├── preload/
│   │   │   └── preload.ts      # Secure IPC bridge
│   │   └── renderer/           # React frontend
│   │       ├── App.tsx
│   │       ├── main.tsx
│   │       ├── components/
│   │       │   ├── layout/     # Sidebar, navigation
│   │       │   ├── features/   # Scanner, Export, Settings pages
│   │       │   └── shared/     # Reusable widgets
│   │       ├── store/          # Redux Toolkit state
│   │       │   └── slices/     # uiSlice, projectSlice, exportSlice
│   │       ├── hooks/          # useAppDispatch, useAppTheme, etc.
│   │       └── utils/          # apiClient, formatters
│   └── package.json
│
├── backend/                     # Python FastAPI backend
│   ├── src/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── routes/         # scanner, export, ai, search, petroleum
│   │   │   └── middleware/     # logging, error handling
│   │   ├── core/
│   │   │   ├── domain/
│   │   │   │   └── entities/   # FileInfo, ProjectScan, ExportJob, ...
│   │   │   ├── services/       # scanner_service, export_orchestrator
│   │   │   └── infrastructure/
│   │   │       ├── pdf/        # PDFBuilder (ReportLab)
│   │   │       ├── parsers/    # CSVParser, ExcelParser, CodeParser
│   │   │       ├── petroleum/  # LASParser, ProductionCSVParser
│   │   │       ├── ai/         # AIDocumenter (Anthropic/OpenAI)
│   │   │       └── storage/    # TempManager
│   │   └── utils/              # config, logging_config
│   ├── tests/
│   │   ├── unit/               # test_scanner_service.py, ...
│   │   └── integration/        # test_api_routes.py, ...
│   └── requirements.txt
│
├── docker/
│   ├── Dockerfile.backend
│   └── docker-compose.yml
│
└── .github/workflows/ci.yml
```

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run in development mode (auto-reload)
python src/main.py --port 8765 --reload
```

### Frontend Setup

```bash
cd electron
npm install

# Start Vite dev server + Electron (two terminals)
npm run dev:renderer            # Terminal 1: Vite on :5173
npm run dev:main                # Terminal 2: compile main.ts
# Then in Terminal 3:
npx electron .
```

### Environment Variables

Create `backend/.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...    # For AI documentation
OPENAI_API_KEY=sk-...           # OpenAI fallback
REPODOC_LOG_LEVEL=DEBUG
REPODOC_TEMP_DIR=/tmp/repodoc
REPODOC_PORT=8765
```

## Adding a New File Type (Plugin)

RepoDoc Pro uses a layered approach for adding file type support.

### Step 1: Register the extension in the scanner

```python
# backend/src/core/services/scanner_service.py

EXTENSION_TO_LANGUAGE[".myext"] = Language.UNKNOWN
EXTENSION_TO_CATEGORY[".myext"] = FileCategory.SOURCE
```

### Step 2: Create a parser

```python
# backend/src/core/infrastructure/parsers/myext_parser.py

class MyExtParser:
    def parse(self, file_path: str) -> dict:
        """Returns dict with: headers, rows, stats, content, etc."""
        ...
```

### Step 3: Add to the export orchestrator

```python
# In export_orchestrator.py, inside _add_file_to_builder():

elif file_info.extension == ".myext":
    result = await asyncio.to_thread(self._myext_parser.parse, str(file_info.path))
    builder.add_custom_section(fi_dict, result)
```

### Step 4: Add a PDF renderer method to PDFBuilder

```python
# In pdf_builder.py
def add_myext_section(self, file_info: dict, parsed: dict) -> None:
    self._story.append(Paragraph(file_info["name"], self.styles["h2"]))
    # ... add flowables
```

## Testing

```bash
# Backend
cd backend
pytest                          # All tests with coverage
pytest tests/unit/              # Unit only
pytest tests/integration/       # Integration only
pytest --cov --cov-report=html  # HTML coverage report

# Frontend
cd electron
npm test
npm run test:coverage
```

## PDF Engine Details

The PDF engine uses **ReportLab** as primary, with custom `Flowable` subclasses:

| Class | Purpose |
|---|---|
| `SyntaxCodeBlock` | Renders code with line numbers using canvas.drawString |
| `FileHeaderBlock` | Styled header card with metadata |
| `PDFBuilder` | Main orchestrator: stories, styles, build() |

Themes are defined as dicts of `colors.HexColor` values:
- `default` — GitHub light-inspired
- `dark` — GitHub dark-inspired
- `github` — Neutral GitHub
- `monokai` — Classic Monokai

## WebSocket Protocol

Export progress is streamed over WebSocket at `/export/ws/{job_id}`.

Server pushes JSON every 500ms:
```json
{
  "progress": 47.3,
  "message": "Processing: api/routes/scanner.py",
  "status": "running",
  "processed_files": 142,
  "total_files": 300,
  "output_files": [],
  "error": null
}
```

Terminal states: `"completed"`, `"failed"`, `"cancelled"`

## Key Design Decisions

**Why ReportLab over WeasyPrint?**
ReportLab gives pixel-perfect control over code blocks, line numbers, and column layouts. WeasyPrint is HTML-based and harder to control programmatically for code rendering.

**Why single FastAPI process?**
Electron launches one backend per application. Multiple workers would require IPC coordination. The async/await model with thread pool for blocking I/O achieves concurrency within one process.

**Why Redux Toolkit?**
The export job lifecycle (pending → running → completed) has complex state transitions. RTK's `createAsyncThunk` + WebSocket hybrid provides both optimistic UI updates and real-time progress.

**Why Electron contextBridge?**
Security. The renderer runs in a sandboxed context. `contextBridge` exposes only the specific IPC calls defined in `preload.ts`, preventing renderer code from accessing Node.js APIs directly.
