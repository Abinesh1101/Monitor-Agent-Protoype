# Live Stream Monitor Agent 🎥🤖

A real-time monitoring system for live TV streams that automatically extracts audio, transcribes speech, and generates concise AI summaries every minute.

![Project Demo](screenshot.png)

## 🎯 Features

- **Live Stream Processing**: Monitors Fox News live stream using HLS (m3u8) rendition links
- **Audio Extraction**: Uses FFMPEG to extract 60-second audio chunks in real-time
- **Speech-to-Text**: Transcribes audio using WhisperX (FREE, no API key required)
- **AI Summarization**: Generates concise summaries (≤15 words) using Hugging Face transformers
- **Real-time UI**: Web interface with Start/Stop controls and live updates
- **Performance**: Processes ~60 seconds of video in ~65-70 seconds (near real-time)

## 🛠️ Technology Stack

**Backend:**

- Python 3.12
- Flask (REST API)
- FFMPEG (audio extraction)
- WhisperX (speech recognition)
- Transformers (BART summarization)

**Frontend:**

- HTML5, CSS3, JavaScript
- Responsive design
- Real-time polling

## 📋 Prerequisites

- Python 3.8+
- FFMPEG installed and in PATH
- 8GB+ RAM recommended
- Internet connection for live stream

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/live-stream-monitor-agent.git
cd live-stream-monitor-agent
```

### 2. Install FFMPEG

**Windows (Chocolatey):**

```bash
choco install ffmpeg
```

**Mac:**

```bash
brew install ffmpeg
```

**Linux:**

```bash
sudo apt install ffmpeg
```

### 3. Set up Python environment

```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### Update Stream URL (Important!)

M3U8 rendition links expire periodically. To get a fresh link:

1. Go to https://www.livenowfox.com/live
2. Open DevTools (F12) → Network tab
3. Filter by `m3u8`
4. Refresh the page
5. Find a link with `rendition.m3u8` in it (NOT master.m3u8)
6. Copy the URL
7. Update `STREAM_URL` in `backend/stream_config.py`

## 🎮 Usage

### Start the application

```bash
cd backend
venv\Scripts\activate  # or source venv/bin/activate
python app.py
```

### Access the UI

Open your browser and go to:

```
http://localhost:5000
```

### Controls

- **START**: Begin monitoring the live stream
- **STOP**: Stop monitoring and save results

## 📊 Output

The system generates:

1. **Audio chunks**: Saved in `backend/data/audio_chunks/`
2. **Transcripts**: Full text transcription of speech
3. **Summaries**: AI-generated summaries (≤15 words)
4. **Records**: JSON file with all data in `backend/data/outputs/records.json`

## 🏗️ Project Structure

```
live-stream-monitor-agent/
├── backend/
│   ├── app.py                    # Flask API server
│   ├── stream_handler.py         # M3U8 extraction & audio processing
│   ├── transcription.py          # WhisperX transcription
│   ├── summarization.py          # AI summarization
│   ├── stream_config.py          # Configuration
│   ├── requirements.txt          # Python dependencies
│   └── data/
│       ├── audio_chunks/         # Extracted audio files
│       └── outputs/              # Transcripts & summaries
├── frontend/
│   ├── index.html               # UI
│   ├── style.css                # Styling
│   └── script.js                # Frontend logic
└── README.md
```

## 🔧 Troubleshooting

### Memory Error

If you encounter `mkl_malloc: failed to allocate memory`:

**Solution:** Use a smaller Whisper model in `stream_config.py`:

```python
WHISPER_MODEL = "tiny"  # Change from "base"
```

### Stream URL Expired

**Error:** `403 Forbidden` or empty audio

**Solution:** Get a fresh rendition link (see Configuration section)

### FFMPEG Not Found

**Error:** `ffmpeg command not found`

**Solution:** Install FFMPEG and ensure it's in your system PATH

## 📈 Performance Metrics

- **Audio Extraction**: ~52 seconds per 60-second chunk
- **Transcription**: ~7-11 seconds (CPU, base model)
- **Summarization**: ~6-7 seconds
- **Total Pipeline**: ~65-70 seconds per minute of video

## 🔐 Notes on Stream Access

- Uses Fox News **rendition links** (not master manifest)
- Links expire every few hours - system attempts auto-refresh
- Manual refresh recommended for extended use
- Respects broadcaster's streaming protocols

## 📝 Assignment Context

This project was developed as a **Monitor Agent Prototype** assignment to demonstrate:

- Live stream processing capabilities
- Real-time audio extraction and analysis
- Speech-to-text transcription
- AI-powered content summarization
- Full-stack development skills

## 🙏 Acknowledgments

- **WhisperX** for fast speech recognition
- **Hugging Face** for pre-trained models
- **FFMPEG** for multimedia processing
- **Fox News** for live stream content

## 📄 License

This project is for educational and demonstration purposes.

## 👤 Author

**Abinesh Sankaranarayanan**

---

⭐ If you found this project helpful, please give it a star!

```

---

## **Additional Files to Include:**

### **.gitignore**
```

# Virtual Environment

venv/
env/
\*.pyc
**pycache**/

# Data files

backend/data/audio_chunks/_.wav
backend/data/outputs/_.json

# OS files

.DS_Store
Thumbs.db

# IDE

.vscode/
.idea/
\*.swp

```

### **requirements.txt** (ensure it's complete)
```

flask==3.0.0
flask-cors==4.0.0
requests==2.31.0
beautifulsoup4==4.12.2
torch>=2.0.0
torchaudio>=2.0.0
transformers>=4.36.0
whisperx @ git+https://github.com/m-bain/whisperx.git
ffmpeg-python==0.2.0
python-dotenv==1.0.0
m3u8==3.5.0
