# RepoDoc Pro

> **Convert any software project into professional PDF documentation — automatically.**

RepoDoc Pro is a production-grade desktop application that recursively scans a code repository and generates beautifully formatted, syntax-highlighted PDF documentation with optional AI-powered summaries, data visualizations, petroleum well log plots, and a clickable table of contents.

**No API key required to use it.** AI summaries are an optional add-on — everything else (scanning, syntax-highlighted PDFs, CSV/Excel previews, petroleum plots, statistics) works out of the box.

---

## ✨ Features

### 📁 Project Scanner
- Full recursive folder tree with file inventory
- Language and file type detection (15+ source types)
- Line counts, file sizes, last-modified dates
- Real-time progress via WebSocket
- Handles repositories with 100,000+ files

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

### 🤖 AI Documentation — *Optional*
Per-file AI summaries powered by **Anthropic Claude** (or OpenAI as fallback). Skipped automatically if no API key is set — exports still complete normally:
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
| **AI (optional)** | Anthropic Claude API, OpenAI API |
| **Architecture** | Clean Architecture, DDD, SOLID |

---

## 🚀 Quick Start

### Requirements

- **Python** 3.10 or higher
- **Node.js** 18 or higher *(only needed for the Electron desktop app — the backend runs standalone as a REST API without it)*

### 1. Clone & Setup

```bash
git clone https://github.com/your-org/repodoc-pro.git
cd repodoc-pro
```

**Linux (any distro)** — auto-detects your package manager (`apt`, `pacman`, `dnf`, `yum`, `zypper`, `apk`, `xbps`, `emerge`, `eopkg`, `nix`); if more than one is found, you'll be prompted to choose:

```bash
bash scripts/setup_dev.sh
```

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1
```

**macOS:**

```bash
bash scripts/setup_dev.sh
```

The script creates a Python virtual environment, installs all backend dependencies, sets up `backend/.env`, and optionally installs the Electron frontend dependencies and runs the test suite.

> **Manual setup instead?** See [Manual Installation](#manual-installation) below.

### 2. (Optional) Add AI API Keys

AI documentation is **disabled by default and not required**. To enable it, edit `backend/.env`:

```bash
# backend/.env
ANTHROPIC_API_KEY=sk-ant-...
# or
OPENAI_API_KEY=sk-...
```

Without a key, exports work normally — AI summary sections are simply omitted.

### 3. Start the Backend

```bash
cd backend
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python src/main.py --port 8765 --reload
```

Verify it's running:

```bash
curl http://localhost:8765/health
```

Expected response:
```json
{"status":"ok","version":"1.0.0","timestamp":"...","python":"..."}
```

> **Note:** the root URL `/` will always return `{"detail":"Not Found"}` — that's expected. Use `/health`, `/docs`, or any of the routes listed in the [API Reference](#-api-reference) below.

Interactive API docs (development mode only): **http://localhost:8765/docs**

### 4. Start the Frontend (Desktop App)

```bash
# Terminal 2
cd electron
npm run dev:renderer

# Terminal 3
cd electron
npx wait-on http://localhost:5173 && npx electron .
```

> Don't need the desktop UI? Skip this step entirely and call the backend directly as a REST API (see [API Reference](#-api-reference)).

---

## 🐙 Running in GitHub Codespaces / Remote Dev Containers

The backend works fine in Codespaces — your forwarded URL replaces `localhost`:

```bash
cd backend
REPODOC_ENV=development python src/main.py --port 8765 --reload
```

Then open the forwarded port URL (shown in the **Ports** tab) and append the route, e.g.:

```
https://<your-codespace-name>-8765.app.github.dev/health
https://<your-codespace-name>-8765.app.github.dev/docs
```

---

## 🛠️ Manual Installation

If you'd rather not use the setup script:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt    # Note the -r flag — required to read the file

cp .env.example .env               # then edit .env as needed

python src/main.py --port 8765 --reload
```

> **Common mistake:** running `pip install requirements.txt` (without `-r`) will fail with *"Could not find a version that satisfies the requirement requirements.txt"*. Always use `pip install -r requirements.txt`.

For the frontend:

```bash
cd electron
npm install
npm run dev:renderer
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
│   │   │       ├── ai/          # AIDocumenter (Claude/OpenAI/Stub — key optional)
│   │   │       └── storage/     # TempManager
│   │   └── utils/               # Settings (pydantic), logging
│   ├── tests/
│   │   ├── unit/                # test_scanner_service, test_pdf_builder, test_parsers
│   │   └── integration/         # test_api_routes (httpx AsyncClient)
│   ├── requirements.txt
│   ├── .env.example
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
│   ├── setup_dev.sh             # Universal Linux/macOS setup (auto-detects distro + package manager)
│   └── setup_dev.ps1            # Windows PowerShell setup
│
└── .github/workflows/ci.yml     # CI/CD: test → build → release → Docker
```

---

## 🔌 API Reference

The FastAPI backend exposes a REST + WebSocket API on `localhost:8765` (or your forwarded Codespaces URL).

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
| `POST` | `/ai/document` | Generate AI docs for a file *(works without a key — returns a stub)* |
| `GET` | `/ai/status` | Check AI provider configuration |
| `GET` | `/search/` | Search files by name/extension/content |
| `GET` | `/petroleum/las/parse` | Parse a LAS well log file |
| `GET` | `/petroleum/las/quicklook` | Generate quick-look plot (PNG path) |
| `GET` | `/petroleum/production/parse` | Parse production CSV |
| `GET` | `/petroleum/production/plot` | Generate rate plots |

> Full interactive docs at `http://localhost:8765/docs` (development mode only — set `REPODOC_ENV=development`)

**Example: scan a project**

```bash
curl -X POST http://localhost:8765/scanner/scan \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/your/project"}'
```

**Example: check AI status**

```bash
curl http://localhost:8765/ai/status
```

```json
{
  "enabled": true,
  "available": false,
  "provider": "none",
  "model": null,
  "has_anthropic_key": false,
  "has_openai_key": false,
  "message": "No API key configured — exports work normally, AI summaries will be skipped."
}
```

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
| `REPODOC_ENV` | `production` | Set to `development` to enable `/docs` |
| `REPODOC_PORT` | `8765` | Backend port |
| `REPODOC_LOG_LEVEL` | `INFO` | Logging verbosity |
| `REPODOC_TEMP_DIR` | `~/.repodoc/temp` | Temp directory |
| `REPODOC_MAX_FILE_SIZE_MB` | `50` | Max file size to process |
| `ANTHROPIC_API_KEY` | *(none)* | **Optional** — enables Claude AI summaries |
| `OPENAI_API_KEY` | *(none)* | **Optional** — OpenAI fallback for AI summaries |
| `REPODOC_AI_MODEL` | `claude-3-5-haiku-20241022` | AI model (only used if a key is set) |

> Neither AI key is required. Leave both blank to use RepoDoc Pro with AI features fully disabled — every other export feature still works.

### Default Exclude Patterns

The scanner automatically skips:
`__pycache__`, `node_modules`, `.git`, `.venv`, `dist`, `build`, `.next`, `coverage`, `*.pyc`, `*.egg-info`

Add custom patterns in **Settings → Scanner Exclude Patterns**.

---

## 🐧 Linux Distro Support

`scripts/setup_dev.sh` works across all major Linux families by auto-detecting available package managers:

| Distro Family | Package Manager Used |
|---|---|
| Arch, Manjaro, EndeavourOS | `pacman` |
| Debian, Ubuntu, Mint, Pop!_OS | `apt` |
| Fedora, RHEL, CentOS Stream | `dnf` |
| Older RHEL/CentOS | `yum` |
| openSUSE | `zypper` |
| Alpine | `apk` |
| Void Linux | `xbps` |
| Gentoo | `emerge` |
| Solus | `eopkg` |
| NixOS / Nix (any distro) | `nix` |

If your system has more than one package manager available, the script presents a menu so you can choose which one to use. If none are found, system dependency installation is skipped and you're prompted to install Python 3.10+, Node.js 18+, and `pango`/`cairo` manually.

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

## 🧯 Troubleshooting

| Symptom | Fix |
|---|---|
| `pip install requirements.txt` fails | Use `pip install -r requirements.txt` (missing `-r` flag) |
| `python: can't open file 'src/main.py'` | You're not in the `backend/` folder — run `cd backend` first |
| `{"detail":"Not Found"}` at root URL | Expected — try `/health` or `/docs` instead of `/` |
| `/ai/status` shows `available: false` | Normal without an API key — add one to `backend/.env` to enable, or ignore it entirely |
| Backend won't start — missing pango/cairo | Re-run `scripts/setup_dev.sh` and choose your package manager when prompted |

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
