# RepoDoc Pro — User Guide

## Getting Started

### 1. Open a Project

Launch RepoDoc Pro and click **"Choose Project Directory"** on the Dashboard, or use **File → Open Project** (⌘O / Ctrl+O).

RepoDoc Pro will automatically:
- Recursively scan all files
- Skip common build artifacts (node_modules, __pycache__, .git, .venv)
- Classify files by language and type
- Count lines of code
- Compute project statistics

### 2. Browse Files (Scanner)

Navigate to the **Project Scanner** tab to:

- **Tree View** — Browse the folder hierarchy
- **List View** — Flat list of all files, searchable
- **Statistics** — Charts showing language distribution, largest files, etc.

Click any source file to preview it with **syntax highlighting**.

Use the search bar to filter by filename or path.

### 3. Export Documentation

Navigate to the **Export** tab.

#### Choose an Export Mode

| Mode | Output | Best For |
|------|--------|----------|
| **Single PDF** | `Project.pdf` | Code reviews, sharing with clients |
| **Folder PDFs** | One PDF per folder | Large projects, modular documentation |
| **Per File** | One PDF per source file | Audit trails, individual file docs |
| **Documentation Package** | Full suite of PDFs | Professional handoffs, portfolios |

#### Configure Content

Toggle what to include:

- **Table of Contents** — Clickable TOC with page numbers
- **Project Statistics** — Language distribution, LOC counts, largest files
- **AI Documentation** — Auto-generated summaries per file (requires API key)
- **Charts & Plots** — Data visualizations for CSV, Excel, petroleum files
- **Syntax Highlighting** — Colorized source code
- **Line Numbers** — Line numbering in code blocks

#### Format Options

- **Paper Size** — A4, Letter, A3
- **Theme** — Default, Dark, GitHub, Monokai
- **Orientation** — Portrait or Landscape
- **Font Size** — 7–14pt for code blocks

#### Choose Output Location

- **Single PDF** → prompts for a save file path
- **Other modes** → prompts for an output folder

Click **Start Export**. Progress is shown in real-time.

---

## AI Documentation

AI-generated summaries require an API key in **Settings**.

### Supported Providers

- **Anthropic Claude** (recommended) — add your `sk-ant-...` key
- **OpenAI GPT-4o mini** (fallback) — add your `sk-...` key

### What AI Generates Per File

- **Summary** — One-sentence description
- **Purpose** — Role in the project
- **Key Functions** — List of important functions/classes
- **Inputs / Outputs** — What the file accepts and returns
- **Dependencies** — Packages and modules used
- **Complexity** — Low / Medium / High / Very High

API keys are stored locally in your OS keychain via electron-store. They are never sent to RepoDoc servers.

---

## Petroleum Data Support

RepoDoc Pro includes specialized support for petroleum engineering file formats.

### LAS Files

LAS (Log ASCII Standard) files will automatically:
- Display the well header (well name, field, location)
- List all curve mnemonics, units, and descriptions
- Show depth range and sample count
- Generate a **quick-look wireline plot** (PNG embedded in PDF)

### Production CSV Files

CSV files containing production data (columns matching oil/gas/water rate patterns) will automatically:
- Generate **oil rate**, **gas rate**, and **water rate** plots
- Show production timeline

### Supported Petroleum Formats

| Format | Parser | Plots |
|--------|--------|-------|
| LAS (.las) | lasio | Quick-look wireline |
| Production CSV | Pandas | Rate vs time |
| DLIS (.dlis) | Planned | — |
| Pressure CSV | Pandas | Pressure trend |

---

## Tips for Large Repositories

- Add aggressive **exclude patterns** in Settings (e.g., `*.min.js`, `migrations/`, `fixtures/`)
- Use **Folder PDFs** mode instead of Single PDF for repos with 10,000+ files
- Disable **AI Documentation** for large repos (costs and time)
- Use the **Statistics** view first to understand what's in the project before exporting

---

## Keyboard Shortcuts

| Action | macOS | Windows/Linux |
|--------|-------|---------------|
| Open Project | ⌘O | Ctrl+O |
| Export Single PDF | ⌘⇧E | Ctrl+Shift+E |
| Toggle Dark Mode | (menu) | (menu) |
| Quit | ⌘Q | Ctrl+Q |

---

## Troubleshooting

**"Backend disconnected" banner appears**
→ Click "Restart Backend" in the banner or go to Settings → Restart Backend.

**Export fails with "Scan failed"**
→ Ensure the project path is still accessible. Check for permission issues.

**AI summaries show "AI documentation not configured"**
→ Add an Anthropic or OpenAI API key in Settings.

**LAS file shows "lasio not installed"**
→ This indicates a missing Python dependency. Reinstall RepoDoc Pro or run `pip install lasio` in the backend venv.

**PDF is very large**
→ Reduce font size, disable images, or use Folder mode to split the output.
