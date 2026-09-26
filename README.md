# 🤖 JARVIS – AI Voice Assistant (Python)

JARVIS is a desktop-based AI-powered voice assistant built using Python. It listens for voice commands, performs system and web-based tasks, and responds using text-to-speech. The project includes a futuristic HUD-style interface and supports AI-driven conversational responses using Groq's free API (Perplexity is also supported).

## 📌 Features

- 🎙️ Wake-word activation — say "Jarvis" and wait, or say it all at once: "Hey Jarvis, open YouTube"
- 🧠 AI-powered answers using Groq's free API (GPT-OSS), with live web search for current events
- 🖥️ Iron Man–style HUD interface with an animated core that reacts when Jarvis is listening, thinking or speaking
- ⌨️ Type commands too — or click a quick-command chip — with a live conversation view
- 🔊 Text-to-speech using Google Text-to-Speech (gTTS)
- 🌐 Open websites (Google, YouTube, LinkedIn, Facebook)
- ▶️ Play songs — opens the top YouTube result
- 🖱️ Open desktop applications by voice
- 📡 Turn Wi-Fi and Bluetooth on/off (Windows, no administrator rights needed)
- 📰 Read top headlines, or news about any topic — say "stop" between headlines to end
- 🧵 Multi-threaded, so the UI stays responsive
- 📦 Build a standalone `.exe` with PyInstaller

## 🗂️ Project Structure

```
JARVIS/
├── main.py            # Core voice assistant logic
├── JARVIS_gui.py      # Desktop window (pywebview) and the bridge to main.py
├── ui/index.html      # The interface: HTML, CSS and the animated core
├── requirements.txt   # Python dependencies
├── .env.example       # Template for your API keys
├── .gitignore         # Ignored files and folders
├── icon.ico           # App icon
├── build_exe.ps1      # PowerShell script to build the EXE
├── JARVIS_gui.spec    # PyInstaller configuration
├── LICENSE            # MIT License
└── README.md          # Project documentation
```

## ⚙️ Technologies Used

| Area | Tools |
| --- | --- |
| Language | Python 3 |
| GUI | pywebview (Edge WebView2), HTML/CSS/Canvas |
| Speech recognition | SpeechRecognition, PyAudio |
| Text-to-speech | gTTS, pygame |
| AI | Groq (GPT-OSS) or Perplexity, via the OpenAI-compatible API |
| Configuration | python-dotenv |
| System control | AppOpener, Windows Radio API (via PowerShell) |
| Packaging | PyInstaller |

## 🔐 Environment Variables

Copy `.env.example` to `.env` in the project root and fill in your keys:

```
AI_PROVIDER=groq                  # or perplexity
GROQ_API_KEY=your_groq_api_key    # free at https://console.groq.com/keys
NEWS_API_KEY=your_newsapi_key     # free at https://newsapi.org
NEWS_COUNTRY=us                   # optional, country for top headlines
```

Optional settings: `AI_MODEL` overrides the provider's default model (Groq: `openai/gpt-oss-20b`), and `AI_WEB_SEARCH=off` turns off Groq's web search. To use Perplexity instead, set `AI_PROVIDER=perplexity` and `PERPLEXITY_API_KEY`. Any other OpenAI-compatible service works with `AI_BASE_URL`, `AI_MODEL` and `AI_API_KEY`.

⚠️ Never commit `.env` — it is listed in `.gitignore`.

## 📦 Installation & Setup

1. Clone the repository
   ```
   git clone https://github.com/iamprathetic/JARVIS.git
   cd JARVIS
   ```
2. Create a virtual environment (recommended)
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Install dependencies
   ```
   pip install -r requirements.txt
   ```
4. Run the application
   ```
   python JARVIS_gui.py
   ```
   Or run without the GUI: `python main.py`

## 🏗️ Build Executable (.exe)

```
.\build_exe.ps1
```

Or manually: `pyinstaller JARVIS_gui.spec`

The `.exe` is created in the `dist/` folder. Your API keys are **not** bundled into it (anyone with the file could extract them), so place a `.env` file next to `JARVIS_gui.exe`, or in `%APPDATA%\Jarvis\.env`.

## 🎤 Example Voice Commands

| Say | What happens |
| --- | --- |
| "Jarvis" | Wakes the assistant (after clicking **Activate**, or pressing **Ctrl + J**) |
| "Hey Jarvis, open Google" | Opens google.com |
| "Play Believer" | Plays the song on YouTube |
| "Open Chrome" / "Open VS Code" | Opens an installed app |
| "List apps" / "Find app spotify" | Lists or searches installed apps |
| "Turn on Wi-Fi" / "Turn off Bluetooth" | Toggles the radio |
| "Read the news" / "Cricket news" / "News about AI" | Reads headlines |
| "What is artificial intelligence?" | Answers with AI |

Note: speech recognition and text-to-speech use Google's online services, so Jarvis needs an internet connection. After "Turn off Wi-Fi" it can't hear you again until Wi-Fi is back on (unless you're on Ethernet).

## 🖥️ Supported Platform

- ✅ Windows 10/11 (fully supported; the interface uses the Edge WebView2 runtime, which Windows 11 includes)
- ⚠️ Linux / macOS (partial — app launching and Wi-Fi/Bluetooth control are not implemented)

## 🚀 Future Enhancements

- System monitoring (CPU, RAM, battery)
- Offline wake-word detection
- Custom skills and plugins
- Cross-platform support

## 👨‍💻 Author

**Prateek Jha** — Aspiring Software Engineer
Tech stack: Python, AI, Desktop Applications, Automation

## 📜 License

Licensed under the [MIT License](LICENSE). You are free to use, modify, and distribute it with attribution.

Feel free to contribute and suggest improvements! If you have any questions or feedback, please open an issue. Enjoy using your AI voice assistant!
