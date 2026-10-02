# OmniMedia User Guide

Welcome to **OmniMedia Extractor**, your all-in-one software for downloading high-resolution photos, carousels, audio tracks, and videos from social media links.

---

## 1. Quick Start

### A. Launch Desktop Graphical User Interface (GUI)
Run the desktop app directly:
```bash
python app.py
```
Or via the CLI shortcut:
```bash
python cli.py --gui
```

### B. Using the Desktop Interface
1. **Paste Link**: Copy a link from Instagram, TikTok, YouTube, Twitter/X, Reddit, Facebook, or Pinterest, and click **Paste**.
2. **Choose Save Directory**: Click **Browse Folder...** to select any directory on your computer where media should be stored.
3. **Select Media Filter**:
   - `All Media`: Downloads all photos, slideshows, and videos in the post.
   - `Photos / Images Only`: Filters only pictures, saving pristine original WebP files and converting companion high-quality JPEGs.
   - `Videos Only`: Downloads only high-definition MP4 video files.
   - `Audio Only (MP3)`: Extracts the audio stream into a pristine MP3 file.
4. **Choose Quality**: Choose between *Highest Available (Best)*, *1080p Full HD*, or *720p HD*.
5. **Click Extract & Download Media**: Progress will show in real-time. Once finished, click **Open Folder** to view your downloaded files immediately in Windows Explorer!

---

## 2. Command Line Interface (CLI) Guide

OmniMedia comes with a full-featured terminal interface.

### Basic Syntax
```bash
python cli.py [URL] [OPTIONS]
```

### Common Commands

#### 1. Download Instagram Post / Carousel with Photos & Videos
```bash
python cli.py "https://www.instagram.com/p/DdoWS1KCGwA/" -o "D:/InstagramDownloads"
```

#### 2. Extract MP3 Audio Only (e.g. YouTube or TikTok Sound)
```bash
python cli.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -f audio -o "D:/Music"
```

#### 3. Download Twitter/X Photos to a Custom Folder and Open Explorer
```bash
python cli.py "https://x.com/username/status/1234567890" -o "C:/Users/User/Pictures" --open-folder
```

#### 4. Save Directly to Selected Folder (Without Creating Author Subfolder)
```bash
python cli.py "https://www.tiktok.com/@user/video/123456" -o "D:/TiktokClips" --no-subfolder
```

#### 5. Check System Status & FFmpeg Detection
```bash
python cli.py --status
```

---

## 3. CLI Options Reference

| Flag | Description | Options / Defaults |
| :--- | :--- | :--- |
| `URL` | Social media post URL (positional argument) | Any supported URL |
| `-o`, `--output-dir` | Target folder to save downloaded media | Defaults to `~/Downloads/OmniMedia` |
| `-f`, `--format` | Filter media type | `all`, `images`, `videos`, `audio` |
| `-q`, `--quality` | Media quality tier | `best`, `high`, `medium` |
| `--subfolder` / `--no-subfolder` | Organize into author/channel subfolders | Default: `True` |
| `--open-folder` | Open folder in Windows Explorer upon completion | Boolean flag |
| `--gui` | Launch PySide6 Desktop GUI | Boolean flag |
| `--status` | Display FFmpeg path, version, and default configs | Boolean flag |

---

## 4. Supported Platforms & Formats

- **Instagram**: Single photos, multiple photo carousels, reels, IGTV, and videos. Saves pristine original WebP and high-resolution JPEG (Quality 95) with complete `metadata.json`.
- **TikTok**: Videos (without watermark), photo carousels/slideshows, background audio MP3 tracks.
- **YouTube / Shorts**: Ultra-HD (4K, 1440p, 1080p, 720p) video with merged audio, or standalone MP3 320kbps audio.
- **Twitter / X**: Original-resolution photo sets, videos, and GIFs.
- **Reddit**: Direct image posts, multi-image galleries, and `v.redd.it` videos with combined audio.
- **Facebook**: Public reels, video posts, and watch links.
- **Pinterest**: High-resolution original pins and video pins.
- **Universal (1000+ sites)**: Automatic fallback to generic extractor for sites like Threads, Vimeo, Twitch, Soundcloud, and more.
