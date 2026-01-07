import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import main

jarvis_thread = None
jarvis_stop_event = threading.Event()

def append_log_ui(speaker, text):
    chat_log.config(state=tk.NORMAL)
    chat_log.insert(tk.END, f"{speaker}: {text}\n")
    chat_log.config(state=tk.DISABLED)
    chat_log.see(tk.END)

def on_heard_callback(command_text):
    root.after(0, lambda: append_log_ui("You", command_text))

def on_speak_callback(response_text):
    root.after(0, lambda: append_log_ui("Jarvis", response_text))
    root.after(0, lambda: set_status("Speaking", "lightblue"))
    def restore_status():
        if jarvis_thread and jarvis_thread.is_alive() and not jarvis_stop_event.is_set():
            set_status("Listening", "lightgreen")
        else:
            set_status("Idle", "orange")
    root.after(1200, restore_status)

def set_status(text, color="white"):
    status_label.config(text=f"Status: {text}", foreground=color)

def run_jarvis():
    main.register_callbacks(on_heard=on_heard_callback, on_speak=on_speak_callback)
    main.start_jarvis(should_continue=lambda: not jarvis_stop_event.is_set())

def start_jarvis_clicked():
    global jarvis_thread, jarvis_stop_event
    if jarvis_thread is None or not jarvis_thread.is_alive():
        jarvis_stop_event.clear()
        jarvis_thread = threading.Thread(target=run_jarvis, daemon=True)
        jarvis_thread.start()
        set_status("Listening", "lightgreen")
        append_log_ui("System", "Jarvis started.")
        mic_button.configure(text="⏹ Stop Jarvis", bootstyle="danger-outline")

def stop_jarvis_clicked():
    jarvis_stop_event.set()
    try:
        main.speech_interrupt.set()
    except Exception:
        pass
    append_log_ui("Jarvis", "Jarvis gonna sleep now")
    try:
        threading.Thread(target=main.speak, args=("Jarvis gonna sleep now",), daemon=True).start()
    except Exception as e:
        print(f"[Stop speak error] {e}")
    set_status("Idle", "orange")
    mic_button.configure(text="🎙 Start Jarvis", bootstyle="success-outline")

def toggle_jarvis():
    if jarvis_thread and jarvis_thread.is_alive():
        stop_jarvis_clicked()
    else:
        start_jarvis_clicked()

def on_exit():
    if messagebox.askokcancel("Exit", "Stop Jarvis and exit?"):
        jarvis_stop_event.set()
        try:
            main.speech_interrupt.set()
        except:
            pass
        root.destroy()

root = ttk.Window(themename="cyborg") 
root.title("Jarvis Assistant")
root.geometry("600x600")
root.resizable(False, False)

title_label = ttk.Label(root, text="🤖 Jarvis Voice Assistant", font=("Helvetica", 20, "bold"))
title_label.pack(pady=(12, 6))

status_label = ttk.Label(root, text="Status: Idle", font=("Helvetica", 12))
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

root.protocol("WM_DELETE_WINDOW", on_exit)
root.mainloop()

