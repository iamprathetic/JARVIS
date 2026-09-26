import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

import ttkbootstrap as ttk

import main

# Jarvis runs on a worker thread; Tkinter may only be touched from the main thread,
# so the worker posts events here and the UI drains them in process_events().
events = queue.Queue()

jarvis_thread = None
stop_event = None  # stop signal for the current session
session_id = 0

STATUS_STYLES = {
    "listening": ('Listening for "Jarvis"', "lightgreen"),
    "awake": ("Listening for your command", "lightgreen"),
    "thinking": ("Thinking", "violet"),
    "speaking": ("Speaking", "lightblue"),
    "idle": ("Idle", "orange"),
}


def resource_path(name):
    """Path to a file bundled by PyInstaller, or next to this script when run from source."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def is_running():
    return stop_event is not None and not stop_event.is_set()


def append_log_ui(speaker, text):
    chat_log.config(state=tk.NORMAL)
    chat_log.insert(tk.END, f"{speaker}: {text}\n")
    chat_log.config(state=tk.DISABLED)
    chat_log.see(tk.END)


def set_status(status):
    if status == "ready":
        status = "listening" if is_running() else "idle"
    elif not is_running() and status != "speaking":
        status = "idle"
    text, color = STATUS_STYLES[status]
    status_label.config(text=f"Status: {text}", foreground=color)


def set_button_running(running):
    if running:
        mic_button.configure(text="⏹ Stop Jarvis", bootstyle="danger-outline")
    else:
        mic_button.configure(text="🎙 Start Jarvis", bootstyle="success-outline")


def process_events():
    try:
        while True:
            event = events.get_nowait()
            if event[0] == "log":
                append_log_ui(event[1], event[2])
            elif event[0] == "status":
                set_status(event[1])
            elif event[0] == "stopped" and event[1] == session_id and is_running():
                # The session ended by itself (e.g. no microphone).
                stop_event.set()
                set_button_running(False)
                set_status("idle")
    except queue.Empty:
        pass
    root.after(100, process_events)


main.register_callbacks(
    on_heard=lambda text: events.put(("log", "You", text)),
    on_speak=lambda text: events.put(("log", "Jarvis", text)),
    on_status=lambda status: events.put(("status", status)),
)


def run_jarvis(session, stop, previous):
    if previous is not None:
        previous.join()  # let the previous session release the microphone first
    if not stop.is_set():
        main.start_jarvis(should_continue=lambda: not stop.is_set())
    events.put(("stopped", session))


def start_jarvis_clicked():
    global jarvis_thread, stop_event, session_id
    session_id += 1
    stop_event = threading.Event()
    jarvis_thread = threading.Thread(target=run_jarvis, args=(session_id, stop_event, jarvis_thread), daemon=True)
    jarvis_thread.start()
    append_log_ui("System", "Jarvis started.")
    set_button_running(True)
    set_status("listening")


def stop_jarvis_clicked():
    stop_event.set()
    main.speech_interrupt.set()
    set_button_running(False)
    set_status("idle")
    threading.Thread(target=main.speak, args=("Jarvis gonna sleep now",),
                     kwargs={"interruptible": False}, daemon=True).start()


def toggle_jarvis():
    if is_running():
        stop_jarvis_clicked()
    else:
        start_jarvis_clicked()


def on_exit():
    if messagebox.askokcancel("Exit", "Stop Jarvis and exit?"):
        if stop_event is not None:
            stop_event.set()
        main.speech_interrupt.set()
        root.destroy()


root = ttk.Window(themename="cyborg")
root.title("Jarvis Assistant")
root.geometry("600x600")
root.resizable(False, False)
try:
    root.iconbitmap(resource_path("icon.ico"))
except tk.TclError:
    pass

title_label = ttk.Label(root, text="🤖 Jarvis Voice Assistant", font=("Helvetica", 20, "bold"))
title_label.pack(pady=(12, 6))

status_label = ttk.Label(root, text="Status: Idle", font=("Helvetica", 12), foreground="orange")
status_label.pack()

btn_frame = ttk.Frame(root)
btn_frame.pack(pady=20)

mic_button = ttk.Button(
    btn_frame,
    text="🎙 Start Jarvis",
    command=toggle_jarvis,
    bootstyle="success-outline",
    width=30
)
mic_button.pack(padx=6, pady=6)

chat_frame = ttk.Frame(root)
chat_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 12))

chat_log = scrolledtext.ScrolledText(
    chat_frame,
    wrap=tk.WORD,
    height=22,
    state=tk.DISABLED,
    font=("Consolas", 11)
)
chat_log.pack(fill=tk.BOTH, expand=True)

exit_button = ttk.Button(root, text="Exit", command=on_exit, bootstyle="secondary-outline")
exit_button.pack(pady=(4, 12))

env_path = os.path.join(main.APP_DIR, ".env")
if not main.PERPLEXITY_API_KEY:
    append_log_ui("System", f"No PERPLEXITY_API_KEY found. Add it to {env_path} to enable AI answers.")
if not main.NEWS_API_KEY:
    append_log_ui("System", f"No NEWS_API_KEY found. Add it to {env_path} to enable news.")

root.protocol("WM_DELETE_WINDOW", on_exit)
root.after(100, process_events)
root.mainloop()
