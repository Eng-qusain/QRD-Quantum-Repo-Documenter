# RepoDoc Pro — Deployment Guide

## Building Desktop Installers

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Node.js | 18+ | For Electron build |
| Python | 3.10+ | For backend venv |
| electron-builder | bundled | Configured in package.json |

### Quick Build (Current Platform)

```bash
# From repo root
cd electron
npm install
npm run dist
# Output: electron/release/
```

### Cross-Platform Builds

**Windows (.exe NSIS installer)**
```bash
npm run dist:win
# Requires: Windows host or Wine on Linux
# Output: release/RepoDoc-Pro-Setup-1.0.0.exe
```

**macOS (.dmg)**
```bash
npm run dist:mac
# Requires: macOS host (code signing for distribution)
# Output: release/RepoDoc-Pro-1.0.0.dmg
```

**Linux (.AppImage + .deb)**
```bash
npm run dist:linux
# Output: release/RepoDoc-Pro-1.0.0.AppImage
#         release/repodoc-pro_1.0.0_amd64.deb
```

### Backend Bundling

`electron-builder` automatically bundles the Python backend via `extraResources` in `package.json`. The backend venv must be created at `backend/.venv` before building:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The main process (`main.ts`) detects the OS and launches the correct Python binary from `.venv`.

---

## Docker Deployment (Backend Only)

For server-side use (headless PDF generation via REST API):

```bash
# Build image
docker build -f docker/Dockerfile.backend -t repodoc-pro-backend ./backend

# Run
docker run -d \
  -p 8765:8765 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e REPODOC_ENV=production \
  -v /projects:/projects:ro \
  --name repodoc-backend \
  repodoc-pro-backend

# Health check
curl http://localhost:8765/health
```

**Using docker-compose:**
```bash
cd docker
ANTHROPIC_API_KEY=sk-ant-... docker-compose up -d
```

---

## macOS Code Signing (Distribution)

```bash
# Set credentials in environment
export APPLE_ID="your@apple.com"
export APPLE_APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"
export APPLE_TEAM_ID="XXXXXXXXXX"
export CSC_LINK="path/to/certificate.p12"
export CSC_KEY_PASSWORD="certificate-password"

cd electron
npm run dist:mac
```

---

## Windows Code Signing

```powershell
$env:CSC_LINK = "path\to\certificate.pfx"
$env:CSC_KEY_PASSWORD = "certificate-password"

cd electron
npm run dist:win
```

---

## Auto-Updates

RepoDoc Pro uses `electron-updater` for automatic updates. Configure in `package.json`:

```json
"publish": {
  "provider": "github",
  "owner": "your-org",
  "repo": "repodoc-pro"
}
```

Publish a GitHub Release → users are notified automatically and shown the `UpdateBanner`.

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `REPODOC_ENV` | `production` | `development` enables API docs at /docs |
| `REPODOC_PORT` | `8765` | Backend HTTP port |
| `REPODOC_LOG_LEVEL` | `INFO` | Python log level |
| `REPODOC_TEMP_DIR` | `~/.repodoc/temp` | Temp file location |
| `ANTHROPIC_API_KEY` | — | Enables Claude AI docs |
| `OPENAI_API_KEY` | — | OpenAI fallback |
| `REPODOC_AI_MODEL` | `claude-3-5-haiku-20241022` | AI model to use |
| `REPODOC_MAX_FILE_SIZE_MB` | `50` | Skip files larger than this |
| `REPODOC_MAX_WORKERS` | `4` | Concurrent worker count |

---

## Performance Tuning

### Large Repositories (50K+ files)

1. **Increase chunk size** (reduces async overhead):
   ```env
   REPODOC_SCAN_CHUNK_SIZE=1000
   ```

2. **Add aggressive exclude patterns** in Settings:
   ```
   *.min.js  *.min.css  *.map
   migrations/  fixtures/  test_data/
   vendor/  third_party/
   ```

3. **Disable AI documentation** for initial pass; enable selectively.

4. **Use Folder PDFs mode** instead of Single PDF for repos > 10K files.

### Memory Usage

Each file's content is held in memory briefly during processing. For repos with many large files, increase `REPODOC_MAX_FILE_SIZE_MB` conservatively.

---

## Troubleshooting Production Issues

**Backend fails to start**
→ Check system deps: `libpango`, `libcairo`, `fonts-liberation` must be installed.

**PDF generation slow**
→ Disable `includeCharts` and `includeArchitecture`; these invoke matplotlib which is slow.

**AI summaries timeout**
→ Anthropic/OpenAI calls have a 30s timeout per file. Reduce scope using `selected_files`.

**AppImage won't launch on Linux**
→ `chmod +x RepoDoc-Pro-*.AppImage && ./RepoDoc-Pro-*.AppImage --no-sandbox`
