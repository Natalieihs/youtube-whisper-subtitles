# YouTube Whisper Subtitles

> 🎬 A Mac desktop app for automatic subtitle generation using Whisper AI

![Platform](https://img.shields.io/badge/platform-macOS-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A beautiful macOS desktop application that downloads YouTube videos and automatically generates Chinese subtitles using OpenAI's Whisper AI with Metal GPU acceleration.

## ✨ Features

- 📥 **Download YouTube Videos** - Extract audio from YouTube videos as MP3
- 🤖 **AI-Powered Subtitles** - Generate high-quality Chinese subtitles using Whisper
- ⚡ **Metal GPU Acceleration** - 20-25x real-time speed on Apple Silicon
- 🖥️ **Native macOS App** - Beautiful GUI with macOS design
- 📦 **Batch Processing** - Process multiple videos at once
- 🎯 **SRT Format** - Standard subtitle format compatible with all video players
- 🚀 **Fast & Efficient** - Process 12-minute audio in ~25-35 seconds

## 🎥 Demo

![App Screenshot](screenshots/app-interface.png)

## 📋 Requirements

- macOS 10.13 or later
- Apple Silicon (M-series) or Intel Mac
- Python 3.10+
- Homebrew

## 🚀 Installation

### 1. Install Dependencies

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install yt-dlp ffmpeg python@3.10
```

### 2. Install Whisper.cpp

```bash
# Clone and build whisper.cpp
cd /tmp
git clone https://github.com/ggml-org/whisper.cpp
cd whisper.cpp
make -j

# Download the model
./models/download-ggml-model.sh base-q5_1
```

### 3. Install Python Dependencies

```bash
pip3 install pyinstaller pillow
```

### 4. Clone This Repository

```bash
git clone https://github.com/Natalieihs/youtube-whisper-subtitles.git
cd youtube-whisper-subtitles
```

### 5. Build the App

```bash
chmod +x build_app.sh
./build_app.sh
```

### 6. Install to Applications

```bash
cp -r dist/YouTube字幕生成器.app /Applications/
```

## 🎯 Usage

### Using the Mac App

1. Launch **YouTube字幕生成器** from Launchpad or Applications folder
2. Paste a YouTube URL in the input field
3. (Optional) Configure output directory and cookies
4. Click **开始处理** (Start Processing)
5. Wait for download and subtitle generation to complete

### Batch Processing

To process multiple videos:
1. Enter URLs in the "批量URL" text area (one per line)
2. Click **开始处理**
3. The app will process them sequentially

### Using Command Line

You can also run the Python script directly:

```bash
python3 youtube_subtitle_generator.py
```

## ⚙️ Configuration

### Output Directory
Default: `~/Downloads/AWS课程`

You can change this in the app settings or modify the code.

### Whisper Model
Default: `base-q5_1` (balanced speed/accuracy)

Available models:
- `tiny-q5_0` - Fastest, ~15 seconds
- `base-q5_1` - Balanced, ~25-35 seconds (recommended)
- `small-q5_1` - More accurate, ~1 minute
- `medium-q5_1` - Best accuracy, ~2-3 minutes

### YouTube Cookies (Optional)

For downloading age-restricted or private videos:

1. Install browser extension "Get cookies.txt LOCALLY"
2. Visit YouTube and log in
3. Export cookies to `~/Downloads/youtube.txt`
4. Enable "使用Cookies" in the app

## 📊 Performance

On Apple M3 Max:
- **12-minute audio**: ~25-35 seconds
- **Speed**: 20-25x real-time
- **CPU usage**: Low (GPU-accelerated)

## 🛠️ Development

### Project Structure

```
youtube-whisper-subtitles/
├── youtube_subtitle_generator.py  # Main application
├── create_icon.py                 # Icon generator
├── build_app.sh                   # Build script
├── app_icon.icns                  # App icon
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

### Building from Source

```bash
# Generate icon
python3 create_icon.py

# Build app
./build_app.sh

# The app will be in dist/YouTube字幕生成器.app
```

## 🐛 Troubleshooting

### "Cannot verify developer" error
```bash
xattr -cr /Applications/YouTube字幕生成器.app
```

### "yt-dlp not found" error
Make sure yt-dlp is installed:
```bash
brew install yt-dlp
```

### "ffmpeg not found" error
Install ffmpeg:
```bash
brew install ffmpeg
```

### Whisper model not found
Download the model:
```bash
cd /tmp/whisper.cpp
./models/download-ggml-model.sh base-q5_1
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp) - Optimized Whisper implementation
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 Contact

- GitHub: [@Natalieihs](https://github.com/Natalieihs)
- Issues: [GitHub Issues](https://github.com/Natalieihs/youtube-whisper-subtitles/issues)

## ⭐ Star History

If you find this project useful, please consider giving it a star!

---

Made with ❤️ for the open source community
