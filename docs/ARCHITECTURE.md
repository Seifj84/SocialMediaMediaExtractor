# OmniMedia System Architecture

## 1. Overview
OmniMedia is a modular, extensible media extraction engine designed to fetch high-resolution photos, original carousels, pristine audio streams, and ultra-high-definition videos from social media platforms.

The system is architected into four decoupled layers:
1. **Interface Layer**: Desktop GUI (PySide6 / Qt), Command Line Interface (Click & Rich), and Web Interface (Streamlit).
2. **Orchestration Layer**: `ExtractorManager` responsible for URL parsing, platform routing, and fallback cascading.
3. **Extraction Engine Layer**: Platform-specific extractors implementing `BaseExtractor`.
4. **Processing & Storage Layer**: Stream chunk downloader, FFmpeg remuxing engine, PIL image transformer, and metadata serializer.

---

## 2. High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph UI["1. User Interface Layer"]
        GUI["PySide6 Desktop GUI (app.py)"]
        CLI["Rich Terminal CLI (cli.py)"]
        WEB["Streamlit Web App (web.py)"]
    end

    subgraph Core["2. Core Orchestration Layer"]
        MGR["ExtractorManager"]
        CFG["Config Engine (~/.omni_media/config.json)"]
        FFMPEG["FFmpeg Locator (imageio-ffmpeg / system)"]
    end

    subgraph Extractors["3. Platform Extractors"]
        IG["Instagram Extractor\n(GraphQL Embed + Fallback)"]
        TT["TikTok Extractor\n(Video + Slideshow + Audio)"]
        YT["YouTube / Shorts Extractor\n(4K/1080p + MP3 320k)"]
        TW["Twitter / X Extractor\n(Orig Photos + MP4)"]
        FB["Facebook Extractor\n(Reels + Videos)"]
        RD["Reddit Extractor\n(Galleries + v.redd.it Audio)"]
        PT["Pinterest Extractor\n(Original Pins)"]
        GEN["Universal Extractor\n(yt-dlp / gallery-dl 1000+ sites)"]
    end

    subgraph Pipeline["4. Processing & Persistence"]
        DOWN["Concurrent Downloader"]
        PIL["PIL Image Engine\n(WebP to Lossless JPEG)"]
        FFM["FFmpeg Audio/Video Merger"]
        META["JSON Metadata Writer"]
        STORAGE["User Selected Destination Folder"]
    end

    GUI --> MGR
    CLI --> MGR
    WEB --> MGR
    CFG --> MGR

    MGR --> IG
    MGR --> TT
    MGR --> YT
    MGR --> TW
    MGR --> FB
    MGR --> RD
    MGR --> PT
    MGR --> GEN

    IG --> DOWN
    TT --> DOWN
    YT --> FFM
    TW --> DOWN
    RD --> DOWN
    FB --> DOWN
    PT --> DOWN
    GEN --> DOWN

    DOWN --> PIL
    DOWN --> FFM
    PIL --> STORAGE
    FFM --> STORAGE
    META --> STORAGE
```

---

## 3. Sequence Flow: Media Extraction Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Desktop GUI / CLI
    participant Mgr as ExtractorManager
    participant Ext as Platform Extractor
    participant FF as FFmpeg Engine
    participant PIL as PIL Image Processor
    participant Disk as Target Directory

    User->>UI: Paste URL & Choose Folder
    UI->>Mgr: extract(url, target_dir, filter, quality)
    Mgr->>Mgr: Match URL regex & route to Extractor
    Mgr->>Ext: extract(...)
    Ext->>Ext: Fetch Post Metadata (GraphQL / API / Embed)
    alt Media contains Video or Audio Extraction
        Ext->>FF: Download and Merge Best Video+Audio / Extract MP3
        FF->>Disk: Write high-def MP4 / MP3
    else Media contains High-Res Photos / Carousel
        Ext->>Disk: Save Pristine Original WebP
        Ext->>PIL: Convert WebP to Companion JPG (Quality 95)
        PIL->>Disk: Save High-Res JPG
    end
    Ext->>Disk: Write metadata.json (Captions, Author, URLs)
    Ext-->>Mgr: ExtractionResult
    Mgr-->>UI: Update Progress & Output Summary
    UI-->>User: Show Download Summary & Provide Explorer Link
```

---

## 4. Key Design Decisions

### A. Non-Freezing Desktop GUI
The PySide6 interface offloads heavy network requests and media merging into an asynchronous `QThread` (`ExtractionWorker`). Signals emit progress updates and status strings back to the Qt main thread without GUI stuttering.

### B. Automatic FFmpeg Discovery
FFmpeg is required for combining high-definition video streams (1080p/4K) with separate audio streams and for converting audio to MP3. Rather than requiring users to manually install FFmpeg, OmniMedia resolves:
1. Environment variables (`FFMPEG_BINARY`).
2. System PATH.
3. Bundled Python binaries via `imageio-ffmpeg`.
4. Standard Windows program directories.

### C. Privacy & Strict Git Hygiene
Downloaded media files often contain user data, personal photos, or large multi-gigabyte binaries. The project structure enforces absolute separation between code and media:
- Output folders (`downloads/`, `output/`, `panganidistrictcouncil/`) are strictly ignored in `.gitignore`.
- Binary extensions (`*.jpg`, `*.mp4`, `*.webp`, `*.mp3`) cannot be committed.
- Configuration containing user filepaths is kept in user-local configuration (`~/.omni_media/config.json`).
