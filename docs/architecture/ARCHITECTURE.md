# RepoDoc Pro — Architecture Documentation

## System Architecture

```
╔══════════════════════════════════════════════════════════════════════╗
║                         USER INTERFACE LAYER                         ║
║                                                                      ║
║  ┌──────────────────────────────────────────────────────────────┐   ║
║  │                    Electron Shell (Node.js)                   │   ║
║  │                                                              │   ║
║  │  main.ts ──── manages ──► Python Backend Process            │   ║
║  │     │                                                        │   ║
║  │     └──── IPC (contextBridge) ──► preload.ts               │   ║
║  │                                        │                    │   ║
║  │                             ┌──────────▼──────────┐         │   ║
║  │                             │   React Renderer     │         │   ║
║  │                             │                      │         │   ║
║  │                             │  Redux Toolkit Store │         │   ║
║  │                             │  ┌───────────────┐  │         │   ║
║  │                             │  │  uiSlice      │  │         │   ║
║  │                             │  │  projectSlice │  │         │   ║
║  │                             │  │  exportSlice  │  │         │   ║
║  │                             │  │  scannerSlice │  │         │   ║
║  │                             │  └───────────────┘  │         │   ║
║  │                             │                      │         │   ║
║  │                             │  Pages:              │         │   ║
║  │                             │  Dashboard           │         │   ║
║  │                             │  Scanner             │         │   ║
║  │                             │  Export              │         │   ║
║  │                             │  Settings            │         │   ║
║  │                             └──────────────────────┘         │   ║
║  └──────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════╝
                         │ HTTP REST + WebSocket
                         │ localhost:8765
╔══════════════════════════════════════════════════════════════════════╗
║                          API LAYER (FastAPI)                         ║
║                                                                      ║
║  GET  /health                                                        ║
║  POST /scanner/scan          WS /scanner/ws                         ║
║  POST /export/start          WS /export/ws/{job_id}                ║
║  GET  /export/{id}/status                                           ║
║  POST /export/{id}/cancel                                           ║
║  POST /ai/document           GET /ai/status                         ║
║  GET  /search/                                                       ║
║  GET  /petroleum/las/parse   GET /petroleum/las/quicklook           ║
║                                                                      ║
║  Middleware: RequestLogging, ErrorHandler, GZip, CORS               ║
╚══════════════════════════════════════════════════════════════════════╝
                         │
╔══════════════════════════════════════════════════════════════════════╗
║                       APPLICATION LAYER (Services)                   ║
║                                                                      ║
║  ┌─────────────────────┐    ┌────────────────────────────────────┐  ║
║  │  ProjectScanner     │    │  ExportOrchestrator                │  ║
║  │  Service            │    │                                    │  ║
║  │                     │    │  Mode A: Single PDF                │  ║
║  │  • Async file walk  │    │  Mode B: Folder PDFs              │  ║
║  │  • Chunked process  │    │  Mode C: Per-file PDFs            │  ║
║  │  • Progress events  │    │  Mode D: Package                  │  ║
║  │  • Cancellation     │    │                                    │  ║
║  │  • Stats compute    │    │  • Job registry                   │  ║
║  └─────────────────────┘    │  • Cancel support                 │  ║
║                             │  • WS progress push               │  ║
║                             └────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════════════════╝
                         │
╔══════════════════════════════════════════════════════════════════════╗
║                        DOMAIN LAYER (Entities)                       ║
║                                                                      ║
║  FileInfo        DirectoryNode    ProjectScan    ProjectStats        ║
║  ExportJob       AIDocumentation  PetroleumWellData                 ║
║  FileCategory    Language         ExportMode                        ║
╚══════════════════════════════════════════════════════════════════════╝
                         │
╔══════════════════════════════════════════════════════════════════════╗
║                      INFRASTRUCTURE LAYER                            ║
║                                                                      ║
║  PDF Engine        Parsers              AI              Petroleum    ║
║  ──────────        ───────              ──              ─────────    ║
║  PDFBuilder        CSVParser            AIDocumenter    LASParser    ║
║  SyntaxCodeBlock   ExcelParser          • Anthropic     ProdParser   ║
║  FileHeaderBlock   CodeParser           • OpenAI                     ║
║                    ImageParser          • Stub mode                  ║
║                                                                      ║
║  Storage                                                             ║
║  ───────                                                             ║
║  TempManager       (manages /tmp/repodoc lifecycle)                 ║
╚══════════════════════════════════════════════════════════════════════╝
```

## Data Flow: Export Pipeline

```
User clicks "Start Export"
        │
        ▼
ExportPage.tsx
  └─ dispatch(startExport({projectPath, options}))
        │
        ▼ POST /export/start
FastAPI ExportRouter
  └─ ExportOrchestratorService.start_export()
        │
        ├─ asyncio.create_task(_run_export())  ← non-blocking
        │
        └─ returns job_id immediately

        │ WebSocket /export/ws/{job_id}
        ▼  (500ms polling)
_run_export() pipeline:
  1. ProjectScannerService.scan()          [0-20%]
  2. AIDocumenter (if enabled)            [20-45%]
  3. PDFBuilder construction              [45-98%]
     └─ Per file: parser → flowables → story
  4. builder.build()                      [98-100%]
        │
        ▼
  output_files = ["/path/to/output.pdf"]
  job.status = "completed"
        │
        ▼ WebSocket push
ExportPage.tsx
  └─ updateJobProgress({status:"completed", outputFiles:[...]})
        │
        ▼
User sees "Export Complete" + "Open Output Folder" button
```

## Scanner Architecture

```
ProjectScannerService.scan(path, exclude_patterns)
        │
        ├─ Phase 1: _collect_paths()           [thread pool]
        │    └─ os.walk() with fnmatch exclude
        │
        ├─ Phase 2: _process_file() × N       [asyncio.gather, chunks of 500]
        │    ├─ stat() for size/mtime
        │    ├─ Extension → language/category classification
        │    ├─ Encoding detection
        │    └─ Line count (text files only)
        │
        ├─ Phase 3: _build_tree()              [thread pool]
        │    └─ Recursive DirectoryNode assembly
        │
        └─ Phase 4: _compute_stats()           [sync, fast]
             ├─ language_distribution
             ├─ extension_distribution
             ├─ category_distribution
             └─ largest_files[]
```

## PDF Builder Architecture

```
PDFBuilder
  │
  ├─ _setup_styles()           → ParagraphStyle dict (h1-h3, body, caption, toc)
  │
  ├─ add_cover_page()          → Paragraph + Table flowables
  ├─ add_toc()                 → TableOfContents flowable
  ├─ add_section_header()      → Paragraph with bookmark
  ├─ add_source_file()         → FileHeaderBlock + SyntaxCodeBlock
  ├─ add_csv_preview()         → Table with styled header rows
  ├─ add_image()               → Image flowable (proportional scale)
  ├─ add_ai_summary()          → Paragraphs with bullet lists
  └─ add_statistics_page()     → Summary Table + distribution data
        │
        ▼
  build()
    └─ SimpleDocTemplate.build(story, onFirstPage=header_footer, ...)
         └─ ReportLab PLATYPUS layout engine → PDF bytes → file
```

## Component Hierarchy (Frontend)

```
App
├─ MainLayout
│   ├─ Sidebar navigation
│   └─ <Routes>
│       ├─ /dashboard  → DashboardPage
│       │               ├─ Stat Cards
│       │               ├─ Language Distribution Chart
│       │               └─ Largest Files List
│       │
│       ├─ /scanner   → ScannerPage
│       │               ├─ Toolbar (search, view toggles)
│       │               ├─ FileTreeView (SimpleTreeView / List)
│       │               └─ CodePreview (SyntaxHighlighter)
│       │               or StatsPanel (when view=stats)
│       │
│       ├─ /export    → ExportPage
│       │               ├─ Export Mode Selector (4 cards)
│       │               ├─ Content Toggles
│       │               ├─ Format Options
│       │               └─ Progress + Actions Panel
│       │
│       └─ /settings  → SettingsPage
│                       ├─ Theme Toggle
│                       ├─ AI API Keys
│                       ├─ Exclude Patterns Manager
│                       └─ Backend Controls
│
├─ BackendStatus banner (polls /health every 10s)
└─ UpdateBanner (shown when update downloaded)
```
