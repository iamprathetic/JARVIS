import base64
import difflib
import os
import platform
import re
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from urllib.parse import quote

import pygame
import requests
import speech_recognition as sr
from dotenv import load_dotenv
from gtts import gTTS
from openai import AuthenticationError, OpenAI as OpenAIClient, RateLimitError

IS_WINDOWS = platform.system() == "Windows"

# Windows consoles often can't print non-English text (e.g. Hindi headlines); don't crash on it.
for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")

if IS_WINDOWS:
    try:
        import AppOpener
    except Exception as e:
        print(f"[AppOpener import error] {e}")
        AppOpener = None
else:
    AppOpener = None


def _app_dir():
    """Folder containing the .exe when frozen by PyInstaller, otherwise this script's folder."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


APP_DIR = _app_dir()

# Keys are read from a .env next to the app (never bundled into the .exe),
# falling back to %APPDATA%\Jarvis\.env.
load_dotenv(os.path.join(APP_DIR, ".env"))
load_dotenv(os.path.join(os.environ.get("APPDATA", ""), "Jarvis", ".env"))

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_COUNTRY = os.getenv("NEWS_COUNTRY", "us")
NEWS_COUNT = 5

on_heard_callback = None
on_speak_callback = None
on_status_callback = None


def register_callbacks(on_heard=None, on_speak=None, on_status=None):
    """on_status receives one of: listening, awake, thinking, speaking, ready."""
    global on_heard_callback, on_speak_callback, on_status_callback
    on_heard_callback = on_heard
    on_speak_callback = on_speak
    on_status_callback = on_status


def _notify(callback, *args):
    if callback:
        try:
            callback(*args)
        except Exception as e:
            print(f"[Callback error] {e}")


# Set to cut off the current speech (e.g. when the user presses Stop).
# It stays set until start_jarvis() clears it, so queued speech is skipped too.
speech_interrupt = threading.Event()
_speak_lock = threading.Lock()

recognizer = sr.Recognizer()
try:
    pygame.mixer.init()
except Exception as e:
    print(f"[Pygame init error] {e}")


def speak(text, interruptible=True):
    text = (text or "").strip()
    if not text or (interruptible and speech_interrupt.is_set()):
        return
    print(f"[Jarvis] {text}")
    _notify(on_speak_callback, text)

    # Only one voice at a time: pygame's music player and the temp file are shared.
    with _speak_lock:
        if interruptible and speech_interrupt.is_set():
            return
        _notify(on_status_callback, "speaking")
        fd, path = tempfile.mkstemp(prefix="jarvis_", suffix=".mp3")
        os.close(fd)
        try:
            gTTS(text).save(path)
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            clock = pygame.time.Clock()
            while pygame.mixer.music.get_busy():
                if interruptible and speech_interrupt.is_set():
                    pygame.mixer.music.stop()
                    break
                clock.tick(10)
        except Exception as e:
            print(f"[TTS/playback error] {e}")
        finally:
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass
            try:
                os.remove(path)
            except OSError:
                pass
        _notify(on_status_callback, "ready")


def listen(timeout, phrase_time_limit):
    """Return what was said in lowercase, or None if nothing understandable was heard."""
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            return None
    try:
        return recognizer.recognize_google(audio).lower()
    except sr.UnknownValueError:
        return None


QUESTION_START = re.compile(r"^(what is|what are|what does|who|why|how|explain|define|meaning of)\b")


def _clean_for_speech(text):
    text = re.sub(r"\s*\[\d+(?:,\s*\d+)*\]", "", text)  # citation markers like [1] or [1, 2]
    text = re.sub(r"\*+|`+|^#+\s*", "", text, flags=re.MULTILINE)  # markdown
    return re.sub(r"\s+", " ", text).strip()


_ai_client = None


def aiProcess(command):
    global _ai_client
    if not PERPLEXITY_API_KEY:
        return "My AI isn't set up yet. Please add a Perplexity API key to the .env file."
    try:
        if _ai_client is None:
            _ai_client = OpenAIClient(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai", timeout=30)
        completion = _ai_client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": (
                    "You are a virtual assistant named Jarvis, skilled in general tasks like Alexa and "
                    "Google Assistant. Your answers are read aloud, so reply in two or three short "
                    "sentences of plain text with no markdown, lists or links."
                )},
                {"role": "user", "content": command}
            ]
        )
        answer = completion.choices[0].message.content or ""
    except (AuthenticationError, RateLimitError) as e:
        print(f"[AI error] {type(e).__name__}: {e}")
        if "quota" in str(e).lower():
            return "My Perplexity account is out of credits. Please add credits to use AI answers."
        if isinstance(e, AuthenticationError):
            return "My Perplexity API key was rejected. Please check the key in the .env file."
        return "I'm getting too many requests right now. Please try again in a moment."
    except Exception as e:
        print(f"[AI error] {type(e).__name__}: {e}")
        return "Sorry, I couldn't reach my AI service right now."
    return _clean_for_speech(answer) or "Sorry, I don't have an answer for that."


def play_on_youtube(song_name):
    """Open the top YouTube result for song_name, falling back to the search page."""
    url = f"https://www.youtube.com/results?search_query={quote(song_name)}"
    try:
        html = requests.get(url, timeout=8, headers={"Accept-Language": "en-US,en;q=0.9"}).text
        match = re.search(r'"videoId":"([\w-]{11})"', html)
        if match:
            url = f"https://www.youtube.com/watch?v={match.group(1)}"
    except requests.RequestException as e:
        print(f"[YouTube search error] {e}")
    webbrowser.open(url)


def _known_app_paths():
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    office = os.path.join(program_files, "Microsoft Office", "root", "Office16")
    vscode = os.path.join(local_app_data, "Programs", "Microsoft VS Code", "Code.exe")
    return {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "paint": "mspaint.exe",
        "terminal": "wt.exe",
        "chrome": os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"),
        "word": os.path.join(office, "WINWORD.EXE"),
        "excel": os.path.join(office, "EXCEL.EXE"),
        "vscode": vscode,
        "vs code": vscode,
        "visual studio code": vscode,
        "steam": os.path.join(program_files_x86, "Steam", "steam.exe"),
        "epic games": os.path.join(program_files_x86, "Epic Games", "Launcher", "Portal", "Binaries", "Win32", "EpicGamesLauncher.exe"),
        "perplexity": os.path.join(local_app_data, "Programs", "Perplexity", "Perplexity.exe"),
    }


def _installed_app_names():
    if AppOpener is None:
        return []
    try:
        return [name for name in AppOpener.give_appnames() if name.strip()]
    except Exception as e:
        print(f"[AppOpener error] {e}")
        return []


def open_application(app_name: str) -> str:
    app_name = app_name.strip().lower()
    if not app_name:
        return "Please tell me which application to open."
    if not IS_WINDOWS:
        return "Opening applications is only supported on Windows right now."

    # Relative names (notepad.exe) are resolved by Windows; absolute paths must exist.
    exe = _known_app_paths().get(app_name)
    if exe and (not os.path.isabs(exe) or os.path.exists(exe)):
        try:
            os.startfile(exe)
            return f"Opening {app_name}"
        except OSError as e:
            print(f"[open_application error] {e}")

    names = _installed_app_names()
    matches = [app_name] if app_name in names else difflib.get_close_matches(app_name, names, n=1, cutoff=0.6)
    if matches:
        try:
            AppOpener.open(matches[0], match_closest=True, output=False)
            return f"Opening {matches[0]}"
        except Exception as e:
            print(f"[AppOpener error] {e}")
    return f"Sorry, I couldn't find an app called {app_name}."


def list_app_names() -> str:
    names = sorted(_installed_app_names())
    if not names:
        return "I couldn't load the list of installed apps."
    print("\n".join(names))
    return f"I know {len(names)} apps. Say find app, followed by a name, to search them."


def find_app(query: str) -> str:
    names = _installed_app_names()
    found = [name for name in names if query in name]
    found += [name for name in difflib.get_close_matches(query, names, n=5, cutoff=0.5) if name not in found]
    if not found:
        return f"I couldn't find any apps matching {query}."
    return "I found: " + ", ".join(found[:5])


# Uses the Windows Radio API, the same switch as the Quick Settings toggles,
# so it works without administrator rights.
_RADIO_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
Function Await($WinRtTask, $ResultType) {
    $task = $asTaskGeneric.MakeGenericMethod($ResultType).Invoke($null, @($WinRtTask))
    $task.Wait(-1) | Out-Null
    $task.Result
}
[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
[Windows.Devices.Radios.RadioState,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
Await ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) ([Windows.Devices.Radios.RadioAccessStatus]) | Out-Null
$radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$radio = $radios | Where-Object { $_.Kind -eq '__KIND__' } | Select-Object -First 1
if (-not $radio) { 'NotFound'; exit }
Await ($radio.SetStateAsync('__STATE__')) ([Windows.Devices.Radios.RadioAccessStatus])
"""


def set_radio(kind: str, turn_on: bool) -> str:
    """kind is 'WiFi' or 'Bluetooth'. Returns a sentence describing the result."""
    label = "Wi-Fi" if kind == "WiFi" else "Bluetooth"
    state = "on" if turn_on else "off"
    if not IS_WINDOWS:
        return f"{label} control is only supported on Windows right now."

    script = _RADIO_SCRIPT.replace("__KIND__", kind).replace("__STATE__", "On" if turn_on else "Off")
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            capture_output=True, text=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"[{label} error] {e}")
        return f"Sorry, I couldn't turn {state} {label}."

    lines = result.stdout.strip().splitlines()
    status = lines[-1].strip() if lines else ""
    if status == "Allowed":
        return f"{label} is now {state}."
    if status == "NotFound":
        return f"I couldn't find a {label} adapter on this computer."
    print(f"[{label} error] status={status!r} {result.stderr.strip()}")
    return f"Sorry, Windows didn't let me turn {state} {label}."


def parse_radio_command(c):
    """Return ('WiFi' | 'Bluetooth', turn_on) for commands like 'turn off wifi', else None."""
    if QUESTION_START.match(c) or not re.search(r"\b(turn|switch|enable|disable)\b", c):
        return None
    if "bluetooth" in c:
        kind = "Bluetooth"
    elif re.search(r"\bwi-?\s?fi\b", c):
        kind = "WiFi"
    else:
        return None
    return kind, not re.search(r"\b(off|disable)\b", c)


NEWS_FILLER = {
    "read", "tell", "me", "the", "latest", "top", "today's", "todays", "get", "give", "show", "some",
    "any", "what's", "whats", "current", "recent", "please", "happening", "in", "can", "you", "us",
}


def parse_news_request(c):
    """Return the news topic ('' for top headlines), or None if c isn't a news request."""
    if not re.search(r"\b(news|headlines)\b", c) or QUESTION_START.match(c):
        return None
    m = re.search(r"\b(?:news|headlines)\s+(?:about|on|for|from|in|regarding)\s+(.+)$", c)
    if m:
        return m.group(1).strip()
    before = re.split(r"\b(?:news|headlines)\b", c, maxsplit=1)[0]
    return " ".join(word for word in before.split() if word not in NEWS_FILLER)


def read_news(topic):
    if not NEWS_API_KEY:
        speak("I need a News API key in the .env file to read the news.")
        return
    if topic:
        url = "https://newsapi.org/v2/everything"
        params = {"q": topic, "language": "en", "sortBy": "publishedAt", "pageSize": NEWS_COUNT}
    else:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"country": NEWS_COUNTRY, "pageSize": NEWS_COUNT}
    try:
        r = requests.get(url, params=params, headers={"X-Api-Key": NEWS_API_KEY}, timeout=10)
        r.raise_for_status()
        articles = r.json().get("articles", [])
    except (requests.RequestException, ValueError) as e:
        print(f"[News error] {e}")
        speak("Sorry, I couldn't fetch the news right now.")
        return

    # Drop removed articles and the " - Source Name" suffix NewsAPI adds to titles.
    titles = [re.sub(r"\s+-\s+[^-]+$", "", a["title"]) for a in articles
              if a.get("title") and a["title"] != "[Removed]"]
    if not titles:
        speak(f"I couldn't find any recent news about {topic}." if topic else "I couldn't find any headlines right now.")
        return

    speak(f"Here are the latest headlines about {topic}." if topic else "Here are today's top headlines.")
    for i, title in enumerate(titles):
        if speech_interrupt.is_set():
            break
        speak(title)
        if i == len(titles) - 1:
            break
        try:
            reply = listen(timeout=2, phrase_time_limit=3)
        except sr.RequestError:
            reply = None
        if reply and any(word in reply for word in ("stop", "cancel", "enough")):
            speak("Okay, stopping the news.")
            break


WEBSITES = {
    "google": "https://google.com",
    "facebook": "https://facebook.com",
    "youtube": "https://youtube.com",
    "linkedin": "https://linkedin.com",
}


def processCommand(c):
    c = c.lower().strip()
    if not c:
        return

    for site, url in WEBSITES.items():
        if f"open {site}" in c:
            speak(f"Opening {site}")
            webbrowser.open(url)
            return

    if c.startswith("play "):
        song = c[len("play "):].strip()
        speak(f"Playing {song} on YouTube")
        play_on_youtube(song)
        return

    if c.startswith(("list apps", "show apps", "list applications")):
        speak(list_app_names())
        return

    m = re.match(r"find (?:the )?(?:apps?|applications?) (?:called |named |for )?(.+)", c)
    if m:
        speak(find_app(m.group(1).strip()))
        return

    radio = parse_radio_command(c)
    if radio:
        kind, turn_on = radio
        if kind == "WiFi" and not turn_on:
            # Speech recognition and text-to-speech both need the internet.
            speak("Turning off Wi-Fi. I won't be able to hear you until it's back on.")
        speak(set_radio(kind, turn_on))
        return

    m = re.match(r"(?:please )?(?:open|launch) (.+)", c)
    if m:
        speak(open_application(m.group(1)))
        return

    topic = parse_news_request(c)
    if topic is not None:
        read_news(topic)
        return

    speak(aiProcess(c))


def extract_command(heard):
    """None if the wake word wasn't said, '' if only the wake word was said, else the command after it."""
    m = re.match(r"(?:(?:hey|hi|ok|okay)\s+)?jarvis\b[\s,.!?]*(.*)", heard)
    return m.group(1).strip() if m else None


def start_jarvis(should_continue=lambda: True):
    speech_interrupt.clear()
    speak("Initializing Jarvis....")
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
    except Exception as e:
        print(f"[Microphone error] {type(e).__name__}: {e}")
        speak("I can't access the microphone. Please check that one is connected.")
        return

    while should_continue():
        try:
            _notify(on_status_callback, "listening")
            heard = listen(timeout=5, phrase_time_limit=5)
            if not heard or not should_continue():
                continue
            print(f"[Heard] {heard}")
            command = extract_command(heard)
            if command is None:
                continue
            if not command:
                speak("Yes?")
                if not should_continue():
                    break
                _notify(on_status_callback, "awake")
                command = listen(timeout=6, phrase_time_limit=10)
                if not command or not should_continue():
                    continue
            print(f"[Command] {command}")
            _notify(on_heard_callback, command)
            _notify(on_status_callback, "thinking")
            processCommand(command)
        except sr.RequestError as e:
            # Usually means no internet connection; wait instead of spinning.
            print(f"[Speech service error] {e}")
            time.sleep(2)
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    start_jarvis()
