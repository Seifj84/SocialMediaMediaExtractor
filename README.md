# OmniMedia - Universal Social Media Media Extractor

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GUI: PySide6](https://img.shields.io/badge/GUI-PySide6%20Qt-green.svg)](https://pypi.org/project/PySide6/)
[![Engine: yt--dlp](https://img.shields.io/badge/Engine-yt--dlp%20%7C%20gallery--dl-orange.svg)](https://github.com/yt-dlp/yt-dlp)
[![Tests: Passing](https://img.shields.io/badge/Tests-8%20Passed-brightgreen.svg)]()

> **OmniMedia** is a production-grade desktop and command-line application that allows you to paste any social media post link and extract high-definition **photos/images**, **audio tracks (MP3)**, and **videos (up to 4K)** with custom folder selection.

---

## 🌟 Key Features

- 📁 **Custom Folder Selection**: Interactively browse and pick any destination folder on your machine where files should be saved, or configure a default directory.
- 🖼️ **Ultra-High Resolution Photos**: Downloads pristine uncompressed original WebP images and converts companion high-quality JPEGs (Quality 95, subsampling 0).
- 🎵 **High-Bitrate Audio Extraction**: Extract background music, voice tracks, and soundtracks directly to 320kbps MP3 or M4A.
- 🎬 **Up to 4K Video Merging**: Automatically combines separate video and audio streams using bundled or system FFmpeg.
- 🖥️ **Modern Desktop GUI (PySide6 / Qt)**: Responsive dark-themed desktop interface with one-click paste, native folder picker, real-time progress bars, and direct "Open Folder" explorer actions.
- ⚡ **Rich Command Line Interface (CLI)**: Full terminal support with colorized output, filters, and batch capabilities.
- 🌐 **Web UI Included**: Optional browser-based interface via Streamlit.
- 🛡️ **Zero-Leak Git Protection**: Comprehensive `.gitignore` safeguards your repository from accidentally committing downloaded media assets.

---

## 📱 Supported Platforms

| Platform | Images / Photos | Videos (HD/4K) | Audio Extraction | Carousels / Albums |
| :--- | :---: | :---: | :---: | :---: |
| **Instagram** | ✅ (Original + JPG) | ✅ (Reels & IGTV) | ✅ | ✅ (Full carousel) |
| **TikTok** | ✅ (Photo Mode) | ✅ (Watermark-free) | ✅ (MP3) | ✅ |
| **YouTube & Shorts** | ✅ (Thumbnails) | ✅ (Up to 4K) | ✅ (MP3 / 320kbps) | ✅ |
| **Twitter / X** | ✅ (Orig quality) | ✅ | ✅ | ✅ (Multi-image) |
| **Reddit** | ✅ (High-res) | ✅ (Merged Audio) | ✅ | ✅ (Galleries) |
| **Facebook** | ✅ | ✅ (Reels / Public) | ✅ | ➖ |
| **Pinterest** | ✅ (Original Pins) | ✅ | ✅ | ➖ |
| **Universal (1000+ sites)** | ✅ | ✅ | ✅ | ✅ |

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Seifj84/SocialMediaMediaExtractor.git
cd SocialMediaMediaExtractor
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

*(Optional) Install package in editable mode:*
```bash
pip install -e .
```

---

## 💻 Usage

### 1. Modern Desktop GUI
Launch the graphical interface:
```bash
python app.py
```
*or:*
```bash
python cli.py --gui
```

**GUI Capabilities:**
- Paste post link directly from clipboard.
- Click **Browse Folder...** to choose destination directory.
- Select format: *All Media*, *Photos Only*, *Videos Only*, or *Audio Only*.
- Click **Extract & Download Media** to see live progress and open output folder when done.

---

### 2. Command Line Interface (CLI)

```bash
# Basic download to default folder (~/Downloads/OmniMedia)
python cli.py "https://www.instagram.com/p/DdoWS1KCGwA/"

# Save to a specific folder
python cli.py "https://www.instagram.com/p/DdoWS1KCGwA/" -o "D:/MyPhotos"

# Extract audio only (MP3) from YouTube or TikTok
python cli.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -f audio -o "D:/Music"

# Download photos only and open folder in Windows Explorer upon completion
python cli.py "https://x.com/username/status/1234567890" -f images --open-folder

# View system status & FFmpeg detection
python cli.py --status
```

---

### 3. Streamlit Web App
To run the browser-based interface:
```bash
streamlit run web.py
```

---

## 🛠️ CLI Options Reference

```text
Usage: cli.py [OPTIONS] [URL]

Options:
  -o, --output-dir PATH       Destination folder to save media.
  -f, --format [all|images|videos|audio]
                              Filter media type (default: all).
  -q, --quality [best|high|medium]
                              Quality tier (default: best).
  --subfolder / --no-subfolder
                              Organize output into author subfolders.
  --open-folder               Open folder in Explorer after completion.
  --gui                       Launch Desktop GUI (PySide6).
  --status                    Display system status and FFmpeg detection.
  -h, --help                  Show this message and exit.
```

---

## 🏗️ Architecture

For technical specifications, sequence diagrams, and design details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

For step-by-step user workflows and FAQs, see [docs/USER_GUIDE.md](docs/USER_GUIDE.md).

---

## 🧪 Testing

Run the test suite using pytest:
```bash
python -m pytest -v
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
