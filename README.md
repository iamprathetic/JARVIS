# 🤖 JARVIS – AI Voice Assistant (Python)

JARVIS is a desktop-based AI-powered voice assistant built using Python. It listens for voice commands, performs system and web-based tasks, and responds using text-to-speech. The project includes a modern GUI and supports AI-driven conversational responses using Perplexity AI.

## 📌 Features

- 🎙️ Wake-word activation — say "Jarvis" and wait, or say it all at once: "Hey Jarvis, open YouTube"
- 🧠 AI-powered answers using the Perplexity API
- 🖥️ Modern desktop GUI built with Tkinter + ttkbootstrap
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
├── JARVIS_gui.py      # GUI interface
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
| GUI | Tkinter, ttkbootstrap |
| Speech recognition | SpeechRecognition, PyAudio |
| Text-to-speech | gTTS, pygame |
| AI | Perplexity AI (OpenAI-compatible API) |
| Configuration | python-dotenv |
| System control | AppOpener, Windows Radio API (via PowerShell) |
| Packaging | PyInstaller |

## 🔐 Environment Variables

Copy `.env.example` to `.env` in the project root and fill in your keys:

```
PERPLEXITY_API_KEY=your_perplexity_api_key
NEWS_API_KEY=your_newsapi_key
NEWS_COUNTRY=us   # optional, country for top headlines
```

⚠️ Never commit `.env` — it is listed in `.gitignore`.

## 📦 Installation & Setup

1. Clone the repository
   ```
   git clone https://github.com/iamprathetic/project1.git
   cd project1
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
| "Jarvis" | Activates the assistant |
| "Hey Jarvis, open Google" | Opens google.com |
| "Play Believer" | Plays the song on YouTube |
| "Open Chrome" / "Open VS Code" | Opens an installed app |
| "List apps" / "Find app spotify" | Lists or searches installed apps |
| "Turn on Wi-Fi" / "Turn off Bluetooth" | Toggles the radio |
| "Read the news" / "Cricket news" / "News about AI" | Reads headlines |
| "What is artificial intelligence?" | Answers with Perplexity AI |

Note: speech recognition and text-to-speech use Google's online services, so Jarvis needs an internet connection. After "Turn off Wi-Fi" it can't hear you again until Wi-Fi is back on (unless you're on Ethernet).

## 🖥️ Supported Platform

- ✅ Windows (fully supported)
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
