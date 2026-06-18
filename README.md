# RepoDoc Pro

> **Convert any software project into professional PDF documentation — automatically.**

RepoDoc Pro is a production-grade desktop application that recursively scans a code repository and generates beautifully formatted, syntax-highlighted PDF documentation with AI-powered summaries, data visualizations, petroleum well log plots, and a clickable table of contents.

---

## ✨ Features

### 📁 Project Scanner
Instantly analyze any repository:
- Full recursive folder tree with file inventory
- Language and file type detection (15+ source types)
- Line counts, file sizes, last-modified dates
- Real-time progress via WebSocket

### 📄 Table of Contents
Auto-generated clickable TOC with folder → file → page number hierarchy.

### 💻 Source Code Export
For `.py`, `.ts`, `.tsx`, `.js`, `.sh`, `.sql`, `.yaml`, `.json`, `.toml`, `.html`, `.css`, `.md` and more:
- Syntax highlighting (4 themes)
- Line numbering
- Wrapped long lines
- File metadata header card

### 📊 Data File Support
- **CSV** — schema, statistics, preview of first N rows
- **Excel (.xlsx/.xls)** — workbook info, sheet list, sheet previews
- **Parquet** — column types and sample rows

### 🖼️ Image & SVG Export
- PNG, JPG, JPEG, WEBP embedded as gallery pages
- SVG rendered directly into PDF at full resolution

### 🛢️ Petroleum Data (Industry-Grade)
| Format | Features |
|--------|----------|
| **LAS** | Header, well info, curve list, quick-look wireline plot |
| **Production CSV** | Oil/gas/water rate vs time plots |
| **Pressure CSV** | Pressure trend charts |

### 🤖 AI Documentation
Per-file AI summaries powered by **Anthropic Claude** (or OpenAI as fallback):
- Summary & Purpose
- Key Functions / Classes
- Inputs & Outputs
- External Dependencies
- Complexity rating (Low → Very High)

### 📈 Project Statistics
- Total files, LOC, size
- Language distribution bar charts
- Largest file leaderboard
- Folder depth distribution

### 🔍 Search
Search by filename, extension, or file content across the project.

### 📦 Export Modes

| Mode | Output | Best For |
|------|--------|----------|
| **A — Single PDF** | `Project.pdf` | Client handoffs, code reviews |
| **B — Folder PDFs** | One PDF per folder | Modular large projects |
| **C — Per-File PDFs** | One PDF per file | Audit trails |
| **D — Documentation Package** | Full suite | Portfolio, technical due diligence |

### 🎨 Themes

| Theme | Style |
|-------|-------|
| `default` | GitHub Light |
| `dark` | GitHub Dark |
| `github` | GitHub Neutral |
| `monokai` | Classic Monokai |

---

## 🖥️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Desktop Shell** | Electron 28 |
| **Frontend** | React 18, TypeScript, Material UI v5 |
| **State Management** | Redux Toolkit |
| **Backend** | Python 3.11, FastAPI, uvicorn |
| **PDF Engine** | ReportLab 4 (custom Flowables) |
| **Data Processing** | Pandas, OpenPyXL, PyArrow |
| **Code Analysis** | Python AST, Pygments, regex |
| **Visualization** | Matplotlib, Plotly |
| **Petroleum** | lasio |
| **AI** | Anthropic Claude API, OpenAI API |
| **Architecture** | Clean Architecture, DDD, SOLID |

---

## 🚀 Quick Start

### Requirements

- **Python** 3.10 or higher
- **Node.js** 18 or higher
- **npm** 9+

### 1. Clone & Setup

```bash
git clone https://github.com/your-org/repodoc-pro.git
cd repodoc-pro

# Linux/macOS
bash scripts/setup_dev.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1
```

### 2. Configure Environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env — add your ANTHROPIC_API_KEY for AI features
```

### 3. Start Development

**Terminal 1 — Backend:**
```bash
cd backend
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python src/main.py --port 8765 --reload
```

**Terminal 2 — Frontend (Vite dev server):**
```bash
cd electron
npm run dev:renderer
```

**Terminal 3 — Electron:**
```bash
cd electron
npx wait-on http://localhost:5173 && npx electron .
```

---

## 📁 Project Structure

```
repodoc-pro/
├── electron/                    # Desktop frontend
│   ├── src/
│   │   ├── main/main.ts         # Electron main: lifecycle, IPC, backend mgmt
│   │   ├── preload/preload.ts   # Secure contextBridge IPC API
│   │   └── renderer/            # React application
│   │       ├── App.tsx
│   │       ├── components/
│   │       │   ├── layout/      # MainLayout, sidebar
│   │       │   ├── features/    # Dashboard, Scanner, Export, Settings
│   │       │   └── shared/      # BackendStatus, UpdateBanner
│   │       ├── store/           # Redux slices (ui, project, export, scanner)
│   │       ├── hooks/           # useAppTheme, useElectronEvents, etc.
│   │       └── utils/           # apiClient (axios)
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.renderer.config.ts
│
├── backend/                     # Python FastAPI backend
│   ├── src/
│   │   ├── main.py              # FastAPI app + uvicorn entrypoint
│   │   ├── api/routes/          # scanner, export, ai, search, petroleum
│   │   ├── core/
│   │   │   ├── domain/entities/ # FileInfo, ProjectScan, ExportJob, ...
│   │   │   ├── services/        # ProjectScannerService, ExportOrchestrator
│   │   │   └── infrastructure/
│   │   │       ├── pdf/         # PDFBuilder, SyntaxCodeBlock, FileHeaderBlock
│   │   │       ├── parsers/     # CSVParser, ExcelParser, CodeParser, ImageParser
│   │   │       ├── petroleum/   # LASParser, ProductionCSVParser
│   │   │       ├── ai/          # AIDocumenter (Claude/OpenAI/Stub)
│   │   │       └── storage/     # TempManager
│   │   └── utils/               # Settings (pydantic), logging
│   ├── tests/
│   │   ├── unit/                # test_scanner_service, test_pdf_builder, test_parsers
│   │   └── integration/         # test_api_routes (httpx AsyncClient)
│   ├── requirements.txt
│   └── pytest.ini
│
├── docker/
│   ├── Dockerfile.backend
│   └── docker-compose.yml
│
├── docs/
│   ├── architecture/ARCHITECTURE.md
│   ├── developer-guide/DEVELOPER_GUIDE.md
│   ├── user-guide/USER_GUIDE.md
│   └── DEPLOYMENT.md
│
├── scripts/
│   ├── setup_dev.sh             # Linux/macOS one-command setup
│   └── setup_dev.ps1            # Windows PowerShell setup
│
└── .github/workflows/ci.yml     # CI/CD: test → build → release → Docker
```

---

## 🔌 API Reference

The FastAPI backend exposes a REST + WebSocket API on `localhost:8765`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/scanner/scan` | Scan a project directory |
| `WS` | `/scanner/ws` | Real-time scan progress |
| `GET` | `/scanner/file-content` | Fetch file content for preview |
| `POST` | `/export/start` | Start an export job |
| `GET` | `/export/{id}/status` | Poll job status |
| `POST` | `/export/{id}/cancel` | Cancel a running job |
| `WS` | `/export/ws/{id}` | Real-time export progress |
| `POST` | `/ai/document` | Generate AI docs for a file |
| `GET` | `/ai/status` | Check AI provider configuration |
| `GET` | `/search/` | Search files by name/extension/content |
| `GET` | `/petroleum/las/parse` | Parse a LAS well log file |
| `GET` | `/petroleum/las/quicklook` | Generate quick-look plot (PNG path) |
| `GET` | `/petroleum/production/parse` | Parse production CSV |
| `GET` | `/petroleum/production/plot` | Generate rate plots |

> Full interactive docs at `http://localhost:8765/docs` (development mode only)

---

## 🧪 Testing

```bash
# Backend — all tests with coverage
cd backend
pytest

# Backend — specific suites
pytest tests/unit/
pytest tests/integration/
pytest tests/unit/test_pdf_builder.py -v

# Frontend — Redux slices
cd electron
npm test

# Frontend — with coverage report
npm run test:coverage
```

Target: **80%+ backend coverage**, **unit tests for all Redux slices**.

---

## 🏗️ Building for Distribution

```bash
# All platforms (run on the target OS)
cd electron
npm run dist

# Platform-specific
npm run dist:win      # → release/*.exe
npm run dist:mac      # → release/*.dmg
npm run dist:linux    # → release/*.AppImage + *.deb
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for code signing, auto-updates, and Docker deployment.

---

## ⚙️ Configuration

### Backend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Enables Claude AI summaries |
| `OPENAI_API_KEY` | — | OpenAI fallback for AI summaries |
| `REPODOC_AI_MODEL` | `claude-3-5-haiku-20241022` | AI model |
| `REPODOC_PORT` | `8765` | Backend port |
| `REPODOC_LOG_LEVEL` | `INFO` | Logging verbosity |
| `REPODOC_MAX_FILE_SIZE_MB` | `50` | Max file size to process |
| `REPODOC_TEMP_DIR` | `~/.repodoc/temp` | Temp directory |

### Default Exclude Patterns

The scanner automatically skips:
`__pycache__`, `node_modules`, `.git`, `.venv`, `dist`, `build`, `.next`, `coverage`, `*.pyc`, `*.egg-info`

Add custom patterns in **Settings → Scanner Exclude Patterns**.

---

## 🗺️ Roadmap

- [ ] DLIS/LIS petroleum format support
- [ ] Dependency graph export (NetworkX → PDF diagram)
- [ ] Architecture diagram auto-generation (module/package view)
- [ ] Git history integration (commit log, blame)
- [ ] Custom PDF templates / branding
- [ ] Team/cloud mode (share scans)
- [ ] VS Code extension integration

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Write tests for your changes
4. Ensure all tests pass: `pytest` + `npm test`
5. Submit a pull request

See [DEVELOPER_GUIDE.md](docs/developer-guide/DEVELOPER_GUIDE.md) for architecture details and adding new file type parsers.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Credits

Built with:
- [Electron](https://electronjs.org) · [React](https://react.dev) · [Material UI](https://mui.com)
- [FastAPI](https://fastapi.tiangolo.com) · [ReportLab](https://reportlab.com)
- [Pandas](https://pandas.pydata.org) · [lasio](https://lasio.readthedocs.io) · [Matplotlib](https://matplotlib.org)
- [Anthropic Claude](https://anthropic.com) · [Pygments](https://pygments.org)

---

<div align="center">

**RepoDoc Pro** — *Professional documentation, automatically.*

</div>
