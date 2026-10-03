from datetime import datetime
import os
import random
import threading
import time
import tkinter as tk
from tkinter import ttk
import webbrowser
import pyttsx3
import speech_recognition as sr
import wikipedia

# Wikipedia auf Deutsch einstellen
wikipedia.set_lang("de")

# ==========================
#   Sprachausgabe
# ==========================
engine = pyttsx3.init()
engine.setProperty("rate", 170)

is_speaking = False
is_listening_active = False
todo_list = []  # Interne Aufgabenliste


def speak(text):
  global is_speaking
  is_speaking = True
  start_wave()
  try:
    log(f"JARVIS: {text}")
    engine.say(text)
    engine.runAndWait()
  except Exception as e:
    print(f"Sprachausgabe-Fehler: {e}")
  finally:
    stop_wave()
    is_speaking = False


# ==========================
#   GUI-Fenster (Stark Industries HUD)
# ==========================
root = tk.Tk()
root.title("J.A.R.V.I.S. - STARK INDUSTRIES HUD v6.0")
root.geometry("1050x700")
root.configure(bg="#02060f")

# Oberer Status-Header
header_frame = tk.Frame(root, bg="#030b1a", bd=1, relief="solid")
header_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

title_label = tk.Label(
    header_frame,
    text="⚡ J.A.R.V.I.S. INTEGRATED SYSTEM v6.0 ⚡",
    font=("Consolas", 16, "bold"),
    bg="#030b1a",
    fg="#00ff66",
)
title_label.pack(side=tk.LEFT, padx=15, pady=8)

status_label = tk.Label(
    header_frame,
    text="Status: SYSTEM BEREIT",
    font=("Consolas", 11, "bold"),
    bg="#030b1a",
    fg="#00ccff",
)
status_label.pack(side=tk.RIGHT, padx=15, pady=8)

# Hauptbereich: Konsole (Links) & Sidebar (Rechts für Aufgaben & Wellenform)
main_frame = tk.Frame(root, bg="#02060f")
main_frame.pack(side=tk.TOP, fill="both", expand=True, padx=10, pady=5)

# Konsolen-Textfeld (Terminal-Look)
console = tk.Text(
    main_frame,
    bg="#010307",
    fg="#00ff66",
    font=("Consolas", 12),
    insertbackground="#00ff66",
    bd=1,
    relief="solid",
)
console.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 8))

# Rechte Sidebar (Aufgabenliste + Wellenform-Animation)
sidebar_frame = tk.Frame(
    main_frame, bg="#030914", bd=1, relief="solid", width=280
)
sidebar_frame.pack(side=tk.RIGHT, fill="y", padx=(8, 0))

todo_title = tk.Label(
    sidebar_frame,
    text="📋 SYSTEM AUFGABEN",
    font=("Consolas", 11, "bold"),
    bg="#030914",
    fg="#00ccff",
)
todo_title.pack(pady=10)

todo_box = tk.Listbox(
    sidebar_frame,
    bg="#010306",
    fg="#00ff66",
    font=("Consolas", 10),
    bd=0,
    selectbackground="#003300",
)
todo_box.pack(
    side=tk.TOP, fill="both", expand=True, padx=10, pady=(0, 10)
)

# Audio-Wellenform Animations-Container in der Sidebar
wave_frame = tk.Frame(sidebar_frame, bg="#030914", height=60)
wave_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

wave_label = tk.Label(
    wave_frame,
    text="AUDIO FREQUENZ",
    font=("Consolas", 9),
    bg="#030914",
    fg="#008844",
)
wave_label.pack()

bars_canvas = tk.Canvas(
    wave_frame, bg="#010306", height=30, bd=0, highlightthickness=0
)
bars_canvas.pack(fill=tk.X, pady=5)
wave_bars = []
for i in range(12):
  b = bars_canvas.create_rectangle(
      i * 20 + 5, 25, i * 20 + 15, 25, fill="#00ff66", outline=""
  )
  wave_bars.append(b)

animation_running = False


def update_wave():
  global animation_running
  if animation_running:
    for b in wave_bars:
      h = random.randint(3, 25)
      bars_canvas.coords(
          b,
          bars_canvas.coords(b)[0],
          30 - h,
          bars_canvas.coords(b)[2],
          30,
      )
    root.after(100, update_wave)


def start_wave():
  global animation_running
  if not animation_running:
    animation_running = True
    update_wave()


def stop_wave():
  global animation_running
  animation_running = False
  for b in wave_bars:
    bars_canvas.coords(b, bars_canvas.coords(b)[0], 28, bars_canvas.coords(b)[2], 30)


def update_todo_display():
  todo_box.delete(0, tk.END)
  for item in todo_list:
    todo_box.insert(tk.END, f"• {item}")


def toggle_listening():
  global is_listening_active
  if not is_listening_active:
    is_listening_active = True
    btn.config(text="🛑 DAUERMODUS STOPPEN", bg="#330000", fg="#ff4444")
    status_label.config(text="Status: LAUSCH-MODUS AKTIV")
    speak("Dauermodus aktiviert. Ich höre ununterbrochen zu, Sir.")
    threading.Thread(target=continuous_listen_loop, daemon=True).start()
  else:
    is_listening_active = False
    btn.config(text="🎤 DAUERMODUS STARTEN", bg="#001a00", fg="#00ff66")
    status_label.config(text="Status: SYSTEM BEREIT")
    speak("Dauermodus beendet.")


# Unteres Kontroll-Panel (Eingabe + Button)
control_frame = tk.Frame(root, bg="#02060f")
control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

input_frame = tk.Frame(control_frame, bg="#02060f")
input_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

entry_box = tk.Entry(
    input_frame,
    font=("Consolas", 13),
    bg="#010307",
    fg="#00ff66",
    insertbackground="#00ff66",
    relief="solid",
    bd=1,
)
entry_box.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5), ipady=4)
entry_box.bind("<Return>", lambda event: handle_text_input())


def handle_text_input():
  text = entry_box.get().strip()
  if text:
    entry_box.delete(0, tk.END)
    threading.Thread(
        target=process_command, args=(text,), daemon=True
    ).start()


send_btn = tk.Button(
    input_frame,
    text="BEFEHL SENDEN ⌨️",
    font=("Consolas", 11, "bold"),
    bg="#001122",
    fg="#00ccff",
    activebackground="#002244",
    activeforeground="#00ccff",
    bd=1,
    relief="raised",
    command=handle_text_input,
)
send_btn.pack(side=tk.RIGHT, ipady=4)

btn = tk.Button(
    control_frame,
    text="🎤 DAUERMODUS STARTEN",
    font=("Consolas", 12, "bold"),
    bg="#001a00",
    fg="#00ff66",
    activebackground="#003300",
    activeforeground="#00ff66",
    bd=2,
    relief="raised",
    command=toggle_listening,
)
btn.pack(side=tk.BOTTOM, fill=tk.X, ipady=4)


def log(text):
  root.after(0, lambda: _safe_log(text))


def _safe_log(text):
  console.insert(tk.END, text + "\n")
  console.see(tk.END)


# ==========================
#   Timer
# ==========================
def start_timer(seconds):
  def timer_thread():
    time.sleep(seconds)
    msg = f"Achtung Sir! Timer von {seconds} Sekunden ist abgelaufen!"
    speak(msg)

  threading.Thread(target=timer_thread, daemon=True).start()


# ==========================
#   Zentrale Befehlsverarbeitung
# ==========================
def process_command(cmd):
  cmd = cmd.lower()
  log(f"Du: {cmd}")

  # 1. Stichwort-Suche mit Minuszeichen (z.B. -leetz)
  if cmd.startswith("-"):
    search_term = cmd[1:].strip()
    try:
      speak(f"Analysiere Daten zu {search_term}...")
      answer = wikipedia.summary(search_term, sentences=2)
      speak(answer)
    except Exception:
      speak(
          f"Keine internen Datenbank-Einträge gefunden. Öffne Web-Recherche"
          f" für {search_term}, Sir."
      )
      url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
      webbrowser.open(url)

  # 2. Aufgaben zur Liste hinzufügen
  elif "aufgabe" in cmd and ("füge" in cmd or "schreib" in cmd or "hinzu" in cmd):
    task = (
        cmd.replace("füge zur aufgabenliste hinzu", "")
        .replace("füge hinzu", "")
        .replace("aufgabe", "")
        .strip()
    )
    if task:
      todo_list.append(task)
      root.after(0, update_todo_display)
      speak(f"Aufgabe '{task}' erfolgreich ins System eingetragen, Sir.")
    else:
      speak("Welche Aufgabe soll ich eintragen, Sir?")

  # 3. Aufgaben anzeigen
  elif "zeige aufgaben" in cmd or "was sind meine aufgaben" in cmd:
    if todo_list:
      speak(
          f"Sie haben aktuell {len(todo_list)} aktive Aufgaben im System, Sir."
      )
      for t in todo_list:
        log(f"-> {t}")
    else:
      speak("Ihre Aufgabenliste ist momentan komplett leer, Sir.")

  # 4. Aufgaben leeren
  elif "lösche aufgaben" in cmd or "aufgaben löschen" in cmd:
    todo_list.clear()
    root.after(0, update_todo_display)
    speak("Aufgabenliste wurde vollständig bereinigt, Sir.")

  # 5. Programme öffnen (VS Code, Discord, WhatsApp, Roblox, Notepad)
  elif cmd.startswith("öffne"):
    target = cmd.replace("öffne", "").strip()
    speak(f"Öffne {target}, Sir.")

    app_mapping = {
        "vs code": "code",
        "visual studio code": "code",
        "code": "code",
        "discord": "discord",
        "whatsapp": "whatsapp",
        "watsapp": "whatsapp",
        "roblox": "roblox-player:",
        "notepad": "notepad",
        "editor": "notepad",
    }

    try:
      matched = False
      for name, exec_cmd in app_mapping.items():
        if name in target:
          if exec_cmd.endswith(":"):
            os.startfile(exec_cmd + "//")
          else:
            os.system(f"start {exec_cmd}")
          matched = True
          break

      if not matched:
        if "." in target:
          if not target.startswith("http"):
            webbrowser.open("https://" + target)
          else:
            webbrowser.open(target)
        else:
          os.startfile(target)
    except Exception as e:
      log(f"Konnte nicht öffnen: {e}")
      speak("Das Programm konnte nicht gestartet werden, Sir.")

  # 6. Websuche
  elif cmd.startswith("suche"):
    query = cmd.replace("suche", "").strip()
    speak(f"Führe Netzsuche nach {query} durch, Sir.")
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)

  # 7. Uhrzeit
  elif "wie spät" in cmd or "uhrzeit" in cmd:
    now = datetime.now().strftime("%H:%M:%S")
    speak(f"Es ist exakt {now}, Sir.")

  # 8. Timer
  elif "timer" in cmd and "auf" in cmd:
    try:
      teil = cmd.split("auf")[1].strip()
      num = int(teil.split()[0])
      speak(f"Timer auf {num} Sekunden gestartet, Sir.")
      start_timer(num)
    except Exception:
      speak("Die Zeitangabe für den Timer konnte nicht verarbeitet werden.")

  else:
    speak(
        "Befehl nicht erkannt, Sir. Nutzen Sie '-' vor Stichwörtern für"
        " Recherchen."
    )


# ==========================
#   Dauermodus-Schleife
# ==========================
def continuous_listen_loop():
  global is_listening_active
  r = sr.Recognizer()
  r.energy_threshold = 300
  r.dynamic_energy_threshold = True

  log(">>> STARK NETZWERK: Dauermodus aktiv...")

  while is_listening_active:
    if is_speaking:
      time.sleep(0.5)
      continue

    try:
      with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.2)
        audio = r.listen(source, timeout=5, phrase_time_limit=10)

      if is_listening_active and not is_speaking:
        cmd = r.recognize_google(audio, language="de-DE")
        process_command(cmd)

    except sr.WaitTimeoutError:
      continue
    except sr.UnknownValueError:
      continue
    except sr.RequestError as e:
      log(f"Spracherkennungs-Fehler: {e}")
      time.sleep(3)
    except Exception as e:
      time.sleep(1)


# ==========================
#   System Start
# ==========================
log("INITIALISIERE STARK HUD PROTOKOLLE...")
speak("J.A.R.V.I.S. Kernel Version 6.0 online. Alle Systeme bereit, Sir.")

root.mainloop()