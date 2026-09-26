import json
import os
import queue
import sys
import threading

import webview

import main

# Jarvis runs on worker threads and posts UI events here; pump_events() forwards
# them to the page once it has loaded.
events = queue.Queue()
ui_ready = threading.Event()
is_maximized = threading.Event()  # pywebview doesn't track this on Windows
window = None

state_lock = threading.Lock()
jarvis_thread = None
stop_event = None  # stop signal for the current voice session
session_id = 0


def resource_path(name):
    """Path to a file bundled by PyInstaller, or next to this script when run from source."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def is_running():
    return stop_event is not None and not stop_event.is_set()


def post(event_type, **data):
    events.put({"type": event_type, **data})


def log(speaker, text):
    post("log", speaker=speaker, text=text)


main.register_callbacks(
    on_heard=lambda text: log("You", text),
    on_speak=lambda text: log("Jarvis", text),
    on_status=lambda status: post("status", status=status),
)


def pump_events():
    ui_ready.wait()
    while True:
        event = events.get()
        try:
            window.evaluate_js(f"jarvisUI.handle({json.dumps(event)})")
        except Exception as e:
            print(f"[UI error] {e}")


def run_jarvis(session, stop, previous):
    if previous is not None:
        previous.join()  # let the previous session release the microphone first
    if not stop.is_set():
        main.start_jarvis(should_continue=lambda: not stop.is_set())
    with state_lock:
        # The session ended by itself (e.g. no microphone) rather than via Stop.
        if session == session_id and not stop.is_set():
            stop.set()
            post("running", value=False)
            post("status", status="idle")


def start_jarvis():
    global jarvis_thread, stop_event, session_id
    log("System", "Jarvis activated.")
    post("running", value=True)
    with state_lock:
        session_id += 1
        stop_event = threading.Event()
        jarvis_thread = threading.Thread(target=run_jarvis, args=(session_id, stop_event, jarvis_thread), daemon=True)
        jarvis_thread.start()


def stop_jarvis():
    with state_lock:
        stop_event.set()
    main.speech_interrupt.set()
    post("running", value=False)
    threading.Thread(target=main.speak, args=("Jarvis gonna sleep now",),
                     kwargs={"interruptible": False}, daemon=True).start()


def run_typed_command(text):
    if not is_running():
        # Stop leaves speech muted until the next start; typed commands should still talk.
        main.speech_interrupt.clear()
    log("You", text)
    post("status", status="thinking")
    try:
        main.processCommand(text)
    except Exception as e:
        print(f"[Command error] {type(e).__name__}: {e}")
        log("System", "Sorry, something went wrong running that command.")
    post("status", status="ready")


class Api:
    """Methods callable from the page as window.pywebview.api.<name>()."""

    def get_state(self):
        messages = []
        env_path = os.path.join(main.APP_DIR, ".env")
        if not main.AI_API_KEY:
            signup = f" Get a free key at {main.AI_SIGNUP_URL}" if main.AI_SIGNUP_URL else ""
            messages.append(["System", f"No {main.AI_KEY_NAME} found. Add it to {env_path} to enable AI answers.{signup}"])
        if not main.NEWS_API_KEY:
            messages.append(["System", f"No NEWS_API_KEY found. Add it to {env_path} to enable news."])
        ai = f"{main.AI_PROVIDER.title()} · {main.AI_MODEL}"
        if main.AI_PROVIDER == "groq" and main.AI_WEB_SEARCH:
            ai += " · web search"
        ui_ready.set()
        return {"running": is_running(), "ai": ai, "messages": messages}

    def toggle(self):
        if is_running():
            stop_jarvis()
        else:
            start_jarvis()

    def send_command(self, text):
        text = (text or "").strip()
        if text:
            threading.Thread(target=run_typed_command, args=(text,), daemon=True).start()

    def minimize(self):
        window.minimize()

    def toggle_maximize(self):
        if is_maximized.is_set():
            window.restore()
        else:
            window.maximize()

    def close(self):
        window.destroy()


def on_closing():
    if stop_event is not None:
        stop_event.set()
    main.speech_interrupt.set()


if __name__ == "__main__":
    window = webview.create_window(
        "J.A.R.V.I.S.",
        url=resource_path(os.path.join("ui", "index.html")),
        js_api=Api(),
        width=1120,
        height=720,
        min_size=(900, 600),
        frameless=True,
        easy_drag=False,
        background_color="#04080f",
    )
    window.events.closing += on_closing
    window.events.maximized += is_maximized.set
    window.events.restored += is_maximized.clear
    webview.start(pump_events)
