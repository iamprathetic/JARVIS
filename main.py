import speech_recognition as sr
import webbrowser
import requests
import platform
import pygame
import os
import subprocess
import ctypes
from openai import OpenAI as OpenAIClient 
from gtts import gTTS
from datetime import date 
from urllib.parse import quote
from dotenv import load_dotenv
from AppOpener import open as open_app_openerr
from threading import Event

on_heard_callback = None
on_speak_callback = None

def register_callbacks(on_heard=None, on_speak=None):
    global on_heard_callback, on_speak_callback
    on_heard_callback = on_heard
    on_speak_callback = on_speak


speech_interrupt = Event()

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
newsapi = os.getenv("NEWS_API_KEY")

recognizer = sr.Recognizer()
try:
    pygame.mixer.init()
except Exception as e:
    print(f"[Pygame init error] {e}")

def speak(text):
    print(f"[DEBUG] Speaking: {text}")
    speech_interrupt.clear()
    try:
        if on_speak_callback:
            try:
                on_speak_callback(text)
            except Exception as e:
                print(f"[Callback on_speak error] {e}")
    except Exception:
        pass

    try:
        tts = gTTS(text)
        tts.save('temp.mp3') 
        pygame.mixer.music.load('temp.mp3')
        pygame.mixer.music.play()
        clock = pygame.time.Clock()
        while pygame.mixer.music.get_busy():
            if speech_interrupt.is_set():
                pygame.mixer.music.stop()
                break
            clock.tick(10)
        pygame.mixer.music.unload()
        if os.path.exists("temp.mp3"):
            try:
                os.remove("temp.mp3")
            except:
                pass
    except Exception as e:
        print(f"[TTS/playback error] {e}")

def aiProcess(command):
    client = OpenAIClient(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")
    completion = client.chat.completions.create(
        model="sonar-pro",
        messages=[
            {"role": "system", "content": "You are a virtual assistant named jarvis skilled in general tasks like Alexa and Google Cloud. Give short responses please"},
            {"role": "user", "content": command}
        ]
    )
    return completion.choices[0].message.content

def search_youtube_and_play(song_name):
    query = quote(song_name)
    url = f"https://www.youtube.com/results?search_query={query}"
    webbrowser.open(url)
def open_application(app_name: str) -> str:
    if not app_name:
        speak(f"Please specify an application to open.")
        return "no app name provided" 
    try:
        app_name = app_name.lower()
        speak(f"Trying to open {app_name}")
        open_app_openerr(app_name, match_closest=True, output=False)
        return f"opening {app_name}"
    except Exception as e:
        print(f"[AppOpener ERROR] Could not open using appopener: {e}")
        speak("cant open app, try again")
    os_name = platform.system()   
    if os_name == "Windows":
        app_paths = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "paint": "mspaint.exe",
            "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            "vscode": r"C:\Users\Prateek\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            "steam" : r"C:\Program Files (x86)\Steam\steam.exe",
            "epic games" : r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
            "perplexity" : r"C:\Users\Prateek\AppData\Local\Programs\Perplexity\Perplexity.exe",
            "terminal" : "wt.exe",
        }
        exe = app_paths.get(app_name.lower())
        try:
            if exe:
               if os.path.isabs(exe):
                if os.path.exists(exe):
                    os.startfile(exe)
                    return f"Opening {app_name}"
            else:
                os.startfile(exe)
                return f"Opening {app_name}"
        except Exception as e:
         print(f"[open_application fallback error] {e}")
        return f"Could not find {app_name} in known paths."
    else:
     return "App opening is only implemented for Windows in this build."
       
def list_app_names() -> str:
    try:
        open_app_openerr("ls")  
        return "Listing known app names in the console."
    except Exception:
        return "Unable to list apps."
def find_app(query: str) -> str:
    try:
        open_app_openerr(f"find {query}")
        return f"Searching for {query} in known applications. Check console for matches."
    except Exception:
        return "Unable to search applications."


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def turn_on_wifi():
    try:
        if platform.system() == "Windows":
            if not is_admin():
                print("⚠️ Please run this program as Administrator.")
                return
            get_interfaces = subprocess.run(
                'netsh interface show interface',
                shell=True,
                capture_output=True,
                text=True
            )

            wifi_name = None
            for line in get_interfaces.stdout.splitlines():
                if "Wi-Fi" in line or "Wireless" in line:
                    wifi_name = line.split()[-1]
                    break

            if not wifi_name:
                print("❌ Could not detect Wi-Fi adapter.")
                return
            cmd = f'netsh interface set interface name="{wifi_name}" admin=ENABLED'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Wi-Fi has been turned ON.")
            else:
                print("❌ Failed to turn on Wi-Fi.")
                print(f"[WiFi ERROR] {result.stderr}\n{result.stdout}")
        else:
            print("Wi-Fi control is only supported on Windows for now.")
    except Exception as e:
        print(f"[WiFi ERROR] {e}")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def turn_on_bluetooth():
    try:
        if platform.system() == "Windows":
            if not is_admin():
                print("⚠️ Please run this program as Administrator.")
                return

            cmd = (
                'PowerShell -Command '
                '"Get-PnpDevice -Class Bluetooth | Enable-PnpDevice -Confirm:$false"'
            )

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Bluetooth has been turned ON.")
            else:
                print("❌ Failed to turn on Bluetooth.")
                print(f"[ERROR] {result.stderr}\n{result.stdout}")
        else:
            print("Bluetooth control is only supported on Windows for now.")
    except Exception as e:
        print(f"[Bluetooth ERROR] {e}")




def processCommand(c):
    c = c.lower()

    if "open google" in c:
        webbrowser.open("https://google.com")

    elif "open facebook" in c:
        webbrowser.open("https://facebook.com")

    elif "open youtube" in c:
        webbrowser.open("https://youtube.com")

    elif "open linkedin" in c:
        webbrowser.open("https://linkedin.com")

    elif c.startswith("play"):
        song = c.replace("play", "").strip()
        speak(f"Searching YouTube for {song}")
        search_youtube_and_play(song)

    elif c.startswith("open "):
         app_name = c.replace("open ", "",1).strip()
         msg=open_application(app_name)
         speak(msg)
         return
    elif c.startswith(("list apps", "show apps", "list applications")):
        msg = list_app_names()
        speak(msg)
        return
    elif c.startswith("find "):
        query = c.replace("find ", "", 1).strip()
        msg = find_app(query)
        speak(msg)
        return
    elif "turn on wifi" in c or "enable wifi" in c:
        turn_on_wifi()

    elif "turn off wifi" in c or "disable wifi" in c:
        print("❌ Wi-Fi OFF not implemented yet")

    elif "turn on bluetooth" in c or "enable bluetooth" in c:
        turn_on_bluetooth()

    elif "turn off bluetooth" in c or "disable bluetooth" in c:
        print("❌ Bluetooth OFF not implemented yet")
    elif "news" in c:
        today = date.today()
        r = requests.get(f"https://newsapi.org/v2/everything?q=tesla&from={today}&sortBy=publishedAt&apiKey={newsapi}")
        if r.status_code == 200:
            data = r.json()
            articles = data.get('articles', [])
            for article in articles:
                speak(article['title'])
                try:
                    with sr.Microphone() as source:
                        print("Listening for stop command...")
                        audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                        response = recognizer.recognize_google(audio).lower()
                        if "stop" in response or "cancel" in response or "enough" in response:
                            speak("Okay, stopping the news.")
                            break
                except:
                    pass
        else:
            speak("Failed to fetch news.")

    else:
        output = aiProcess(c)
        speak(output)
def start_jarvis(should_continue=lambda: True):
    speak("Initializing Jarvis....")
    while should_continue():
        r = sr.Recognizer() 
        print("recognizing...")
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
            word = r.recognize_google(audio)
            print(f"[Heard] {word}")
            if word.lower() in ["jarvis", "hey jarvis"]:
                speak("Yes?")
                with sr.Microphone() as source:
                    print("Jarvis Active...")
                    audio = r.listen(source)
                    command = r.recognize_google(audio)
                    print(f"[Command] {command}")
                    try:
                        if on_heard_callback:
                            try:
                                on_heard_callback(command)
                            except Exception as e:
                                print(f"[Callback on_heard error] {e}")
                    except Exception:
                        pass
                    processCommand(command)
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")