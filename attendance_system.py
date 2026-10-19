# =====================================================================
#  AI Attendance Tracker
# (face_recognition + OpenCV) with Tkinter dashboard
# =====================================================================
import os
import re
import sys
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk

# Lets Python find a local copy of face_recognition placed next to this file
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import face_recognition

import cv2
import numpy as np
from PIL import Image, ImageTk

# ---------------------------------------------------------------------
# 1. SETTINGS (change them as to ur liking)
# ---------------------------------------------------------------------
STUDENTS_DIR = 'students'
CAMERA_INDEX = 0

TOLERANCE = 0.48        # Max face distance to accept a match (lower = stricter)
MARGIN = 0.06           # Best student must beat the runner-up by at least this much
CONFIRM_FRAMES = 6      # Processed frames a face must match before marking present
PROCESS_EVERY = 3       # Run recognition on every Nth camera frame (keeps UI smooth)
DETECT_SCALE = 0.5      # Shrink factor for detection (0.5 is more accurate than 0.25)
ENROLL_JITTERS = 10     # Extra samples per student photo (slower startup, better accuracy)

VIDEO_MAX_W, VIDEO_MAX_H = 640, 480
IMAGE_EXTS = ('.jpg', '.jpeg', '.png')

# Theme colors (Tkinter, hex)
BG = "#0f172a"
PANEL = "#1e293b"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
GREEN = "#22c55e"
AMBER = "#f59e0b"
RED = "#ef4444"

# Box colors for OpenCV (BGR order)
CV_GREEN = (94, 197, 34)
CV_AMBER = (11, 158, 245)
CV_RED = (68, 68, 239)
FONT = cv2.FONT_HERSHEY_DUPLEX

# ---------------------------------------------------------------------
# 2. LOAD STUDENT PHOTOS
#    Supported layouts:
#      students/john.jpg                (one photo)
#      students/john_1.jpg, john_2.jpg  (several photos, same student)
#      students/john/anything.jpg       (a folder per student)
# ---------------------------------------------------------------------
def clean_name(stem):
    """'john_2' -> 'john'. Only a trailing _number is removed."""
    return re.sub(r'_\d+$', '', stem)


def load_students():
    people = {}
    if not os.path.isdir(STUDENTS_DIR):
        os.makedirs(STUDENTS_DIR)
        print(f"Created empty '{STUDENTS_DIR}' folder. Add student photos and restart.")
        return people

    for entry in sorted(os.listdir(STUDENTS_DIR)):
        path = os.path.join(STUDENTS_DIR, entry)
        if os.path.isdir(path):
            name = entry
            files = [os.path.join(path, f) for f in sorted(os.listdir(path))]
        else:
            name = clean_name(os.path.splitext(entry)[0])
            files = [path]

        for file_path in files:
            if not file_path.lower().endswith(IMAGE_EXTS):
                continue

            image = face_recognition.load_image_file(file_path)

            # Downscale very large photos so detection is fast and reliable
            h, w = image.shape[:2]
            if max(h, w) > 1000:
                scale = 1000 / max(h, w)
                image = cv2.resize(image, (0, 0), fx=scale, fy=scale)

            locations = face_recognition.face_locations(image)
            if len(locations) != 1:
                print(f"  Skipped {file_path}: found {len(locations)} faces (need exactly 1)")
                continue

            encoding = face_recognition.face_encodings(
                image, locations, num_jitters=ENROLL_JITTERS, model="large")[0]
            people.setdefault(name, []).append(encoding)

    return people


print("Loading student profiles (this can take a moment)...")
people = load_students()
person_names = sorted(people.keys())
person_encodings = [people[n] for n in person_names]
print(f"Loaded {len(person_names)} students "
      f"({sum(len(e) for e in person_encodings)} photos).")

# ---------------------------------------------------------------------
# 3. ATTENDANCE LOG (CSV)
# ---------------------------------------------------------------------
current_date = datetime.now().strftime("%Y-%m-%d")
csv_filename = f"Attendance_{current_date}.csv"
recorded = {}   # name -> time marked present

if not os.path.exists(csv_filename) or os.stat(csv_filename).st_size == 0:
    with open(csv_filename, 'w', newline='') as f:
        csv.writer(f).writerow(['Name', 'Time', 'Date'])
else:
    # If the app restarts, remember who was already marked present today
    with open(csv_filename, 'r') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row:
                recorded[row[0]] = row[1] if len(row) > 1 else "Logged"

# ---------------------------------------------------------------------
# 4. CAMERA
# ---------------------------------------------------------------------
video_capture = cv2.VideoCapture(CAMERA_INDEX)
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
if not video_capture.isOpened():
    sys.exit("Could not open the camera. Check that it is connected and not used by another app.")

# ---------------------------------------------------------------------
# 5. USER INTERFACE
# ---------------------------------------------------------------------
root = tk.Tk()
root.title("Smart Attendance Dashboard")
root.geometry("1280x740")
root.minsize(1100, 660)
root.configure(bg=BG)

# Header
header = tk.Frame(root, bg=PANEL, height=70)
header.pack(side=tk.TOP, fill=tk.X)
header.pack_propagate(False)
tk.Label(header, text="Smart Attendance Dashboard", font=("Segoe UI", 20, "bold"),
         bg=PANEL, fg=TEXT).pack(side=tk.LEFT, padx=24)
clock_label = tk.Label(header, font=("Segoe UI", 12), bg=PANEL, fg=MUTED)
clock_label.pack(side=tk.RIGHT, padx=24)

# Footer / status bar
status_var = tk.StringVar()
if person_names:
    status_var.set(f"Camera running  |  {len(person_names)} students enrolled")
else:
    status_var.set("No students loaded. Add photos to the 'students' folder and restart.")
tk.Label(root, textvariable=status_var, anchor="w", bg=PANEL, fg=MUTED,
         font=("Segoe UI", 10), padx=24, pady=8).pack(side=tk.BOTTOM, fill=tk.X)

# Body
body = tk.Frame(root, bg=BG)
body.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
body.columnconfigure(1, weight=1)
body.rowconfigure(0, weight=1)

# Left: camera card
left_panel = tk.Frame(body, bg=PANEL)
left_panel.grid(row=0, column=0, sticky="n", padx=(0, 20))
tk.Label(left_panel, text="Live Camera", font=("Segoe UI", 14, "bold"),
         bg=PANEL, fg=TEXT).pack(anchor="w", padx=16, pady=(14, 8))

placeholder = tk.PhotoImage(width=VIDEO_MAX_W, height=VIDEO_MAX_H)
video_label = tk.Label(left_panel, image=placeholder, bg="#000000")
video_label.image = placeholder
video_label.pack(padx=16)

legend = tk.Frame(left_panel, bg=PANEL)
legend.pack(anchor="w", padx=16, pady=(10, 14))
for color, text in ((GREEN, "Present"), (AMBER, "Verifying"), (RED, "Not Recognized")):
    tk.Label(legend, text="\u25cf", fg=color, bg=PANEL, font=("Segoe UI", 12)).pack(side=tk.LEFT)
    tk.Label(legend, text=text + "   ", fg=MUTED, bg=PANEL, font=("Segoe UI", 10)).pack(side=tk.LEFT)

# Right: stats + roster
right_panel = tk.Frame(body, bg=BG)
right_panel.grid(row=0, column=1, sticky="nsew")


def make_card(parent, title, color, last=False):
    card = tk.Frame(parent, bg=PANEL)
    card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 0 if last else 12))
    value = tk.Label(card, text="0", font=("Segoe UI", 28, "bold"), bg=PANEL, fg=color)
    value.pack(anchor="w", padx=16, pady=(10, 0))
    tk.Label(card, text=title, font=("Segoe UI", 10), bg=PANEL, fg=MUTED).pack(
        anchor="w", padx=16, pady=(0, 10))
    return value


stats_row = tk.Frame(right_panel, bg=BG)
stats_row.pack(fill=tk.X)
total_value = make_card(stats_row, "Total Students", TEXT)
present_value = make_card(stats_row, "Present", GREEN)
absent_value = make_card(stats_row, "Absent", RED, last=True)

table_card = tk.Frame(right_panel, bg=PANEL)
table_card.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
tk.Label(table_card, text="Live Class Roster", font=("Segoe UI", 14, "bold"),
         bg=PANEL, fg=TEXT).pack(anchor="w", padx=16, pady=(14, 8))

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                rowheight=36, font=("Segoe UI", 12), borderwidth=0)
style.configure("Treeview.Heading", background="#334155", foreground=TEXT,
                font=("Segoe UI", 12, "bold"), relief="flat")
style.map("Treeview", background=[("selected", "#334155")])
style.map("Treeview.Heading", background=[("active", "#475569")])

tree_frame = tk.Frame(table_card, bg=PANEL)
tree_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

columns = ('Name', 'Status', 'Time')
tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
tree.heading('Name', text='Student Name')
tree.heading('Status', text='Status')
tree.heading('Time', text='Time In')
tree.column('Name', width=220, anchor=tk.W)
tree.column('Status', width=140, anchor=tk.CENTER)
tree.column('Time', width=140, anchor=tk.CENTER)
tree.tag_configure("present", foreground=GREEN)
tree.tag_configure("absent", foreground="#f87171")

scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

tree_items = {}
for name in person_names:
    if name in recorded:
        item = tree.insert('', tk.END, values=(name, "\u2714 Present", recorded[name]), tags=("present",))
    else:
        item = tree.insert('', tk.END, values=(name, "\u2716 Absent", "--"), tags=("absent",))
    tree_items[name] = item


def refresh_stats():
    total = len(person_names)
    present = len([n for n in person_names if n in recorded])
    total_value.config(text=str(total))
    present_value.config(text=str(present))
    absent_value.config(text=str(total - present))


def update_clock():
    clock_label.config(text=datetime.now().strftime("%A, %d %B %Y   %H:%M:%S"))
    root.after(1000, update_clock)


# ---------------------------------------------------------------------
# 6. RECOGNITION LOGIC
# ---------------------------------------------------------------------
match_counts = {}
last_results = []
frame_count = 0
running = True


def mark_present(name):
    current_time = datetime.now().strftime("%H:%M:%S")
    with open(csv_filename, 'a', newline='') as f:
        csv.writer(f).writerow([name, current_time, current_date])
    recorded[name] = current_time
    tree.item(tree_items[name], values=(name, "\u2714 Present", current_time), tags=("present",))
    refresh_stats()
    status_var.set(f"{name} marked present at {current_time}")


def identify(face_encoding):
    """Return the student's name, or None if the face is unknown or ambiguous."""
    if not person_encodings:
        return None

    # Best distance per student (uses all of that student's photos)
    distances = np.array([
        face_recognition.face_distance(encs, face_encoding).min()
        for encs in person_encodings
    ])
    order = np.argsort(distances)
    best = distances[order[0]]
    second = distances[order[1]] if len(order) > 1 else 1.0

    # Must be close enough AND clearly better than the next different student
    if best <= TOLERANCE and (second - best) >= MARGIN:
        return person_names[order[0]]
    return None


def process(frame):
    """Detect and identify faces. Returns a list of (box, label, color)."""
    small = cv2.resize(frame, (0, 0), fx=DETECT_SCALE, fy=DETECT_SCALE)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    locations = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, locations, model="large")

    inv = 1.0 / DETECT_SCALE
    results = []
    seen = set()

    for encoding, (top, right_edge, bottom, left) in zip(encodings, locations):
        box = (int(left * inv), int(top * inv), int(right_edge * inv), int(bottom * inv))
        name = identify(encoding)

        if name is None:
            results.append((box, "Not Recognized", CV_RED))
            continue

        seen.add(name)
        if name in recorded:
            results.append((box, f"{name} - Present", CV_GREEN))
        else:
            match_counts[name] = match_counts.get(name, 0) + 1
            if match_counts[name] >= CONFIRM_FRAMES:
                mark_present(name)
                results.append((box, f"{name} - Present", CV_GREEN))
            else:
                results.append((box, f"{name} ({match_counts[name]}/{CONFIRM_FRAMES})", CV_AMBER))

    # Anyone not seen this round slowly loses progress
    for n in list(match_counts):
        if n not in seen:
            match_counts[n] = max(0, match_counts[n] - 1)

    return results


def draw_results(frame, results):
    frame_h = frame.shape[0]
    for (left, top, right_edge, bottom), label, color in results:
        cv2.rectangle(frame, (left, top), (right_edge, bottom), color, 2)

        (text_w, text_h), _ = cv2.getTextSize(label, FONT, 0.6, 1)
        label_h = text_h + 14
        label_top = bottom if bottom + label_h <= frame_h else top - label_h
        cv2.rectangle(frame, (left, label_top), (left + text_w + 12, label_top + label_h),
                      color, cv2.FILLED)
        cv2.putText(frame, label, (left + 6, label_top + text_h + 5), FONT, 0.6,
                    (255, 255, 255), 1, cv2.LINE_AA)


def update_frame():
    global frame_count, last_results
    if not running:
        return

    ret, frame = video_capture.read()
    if ret:
        frame = cv2.flip(frame, 1)  # mirror view feels more natural
        frame_count += 1

        if frame_count % PROCESS_EVERY == 0:
            last_results = process(frame)
        draw_results(frame, last_results)

        # Fit the frame into the video panel, keeping the aspect ratio
        h, w = frame.shape[:2]
        scale = min(VIDEO_MAX_W / w, VIDEO_MAX_H / h)
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

    root.after(15, update_frame)


def on_close():
    global running
    running = False
    video_capture.release()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_close)

refresh_stats()
update_clock()
update_frame()
root.mainloop()
