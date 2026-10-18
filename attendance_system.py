# --- THE FIX IMPORTS ---
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import face_recognition

# --- STANDARD IMPORTS ---
import cv2
import numpy as np
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# --- 1. Configuration ---
STUDENTS_DIR = 'students'
known_face_encodings = []
known_face_names = []

print("Loading student profiles...")
for filename in os.listdir(STUDENTS_DIR):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        img_path = os.path.join(STUDENTS_DIR, filename)
        image = face_recognition.load_image_file(img_path)
        encodings = face_recognition.face_encodings(image)
        
        if len(encodings) > 0:
            known_face_encodings.append(encodings[0])
            known_face_names.append(os.path.splitext(filename)[0])

print(f"Loaded {len(known_face_names)} students.")

TOLERANCE = 0.45       # Stricter than before
MARGIN = 0.08          # Best match must beat the runner-up by this much
CONFIRM_FRAMES = 15    # Consecutive frames needed before marking present

# --- 2. Prepare the Excel/CSV Log ---
current_date = datetime.now().strftime("%Y-%m-%d")
csv_filename = f"Attendance_{current_date}.csv"
recorded_students = set()

if not os.path.exists(csv_filename) or os.stat(csv_filename).st_size == 0:
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Time', 'Date'])
else:
    # If the app restarts, remember who was already marked present today
    with open(csv_filename, 'r') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row: recorded_students.add(row[0])

# --- 3. Build the Application UI ---
root = tk.Tk()
root.title("Teacher's Attendance Dashboard")
root.geometry("1000x600")
root.configure(bg="#1e272e") # Dark theme background

# Left Frame for Video
video_frame = tk.Frame(root, bg="#1e272e")
video_frame.pack(side=tk.LEFT, padx=20, pady=20)

video_label = tk.Label(video_frame, bg="#7e241e")
video_label.pack()

# Right Frame for Data Dashboard
data_frame = tk.Frame(root, bg="#8e281e")
data_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)

title_label = tk.Label(data_frame, text="Live Class Roster", font=("Helvetica", 30, "bold"), bg="#1e272e", fg="white")
title_label.pack(pady=10)

# Create the Table (Treeview)
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", rowheight=30, font=("Helvetica", 12))
style.configure("Treeview.Heading", font=("Helvetica", 14, "bold"))

columns = ('Name', 'Status', 'Time')
tree = ttk.Treeview(data_frame, columns=columns, show='headings', height=15)
tree.heading('Name', text='Student Name')
tree.heading('Status', text='Status')
tree.heading('Time', text='Time In')

tree.column('Name', width=150, anchor=tk.CENTER)
tree.column('Status', width=120, anchor=tk.CENTER)
tree.column('Time', width=120, anchor=tk.CENTER)
tree.pack(fill=tk.BOTH, expand=True)

# Populate the table with all students
tree_items = {}
for name in known_face_names:
    if name in recorded_students:
        item = tree.insert('', tk.END, values=(name, "✅ Present", "Already Logged"))
    else:
        item = tree.insert('', tk.END, values=(name, "❌ Absent", "--"))
    tree_items[name] = item # Save the row ID so we can update it later

# --- 4. Camera Loop Inside the UI ---
video_capture = cv2.VideoCapture(0)

def update_frame():
    ret, frame = video_capture.read()
    if ret:
        # Shrink the image for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        seen_names = set()

        for face_encoding, face_location in zip(face_encodings, face_locations):
            name = "Not Recognized"

            if len(known_face_encodings) > 0:
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)

                # Only accept the match if it is close enough
                if face_distances[best_match_index] <= TOLERANCE:
                    name = known_face_names[best_match_index]

            if name != "Not Recognized":
                seen_names.add(name)

                if name not in recorded_students:
                    match_counts[name] = match_counts.get(name, 0) + 1

                    # Only log after several consecutive confirmations
                    if match_counts[name] >= CONFIRM_FRAMES:
                        current_time = datetime.now().strftime("%H:%M:%S")

                        with open(csv_filename, 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([name, current_time, current_date])

                        recorded_students.add(name)
                        tree.item(tree_items[name], values=(name, "✅ Present", current_time))

            # Draw boxes around the face
            top, right, bottom, left = [coord * 4 for coord in face_location]
            color = (70, 110, 38) if name != "Not Recognized" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

        # Reset the counter for anyone not seen this frame
        for n in list(match_counts):
            if n not in seen_names:
                match_counts[n] = 0

            # Draw boxes around the face
            top, right, bottom, left = [coord * 4 for coord in face_location]
            color = (70, 110, 38) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

        # Convert OpenCV image to Tkinter image format
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        
        # Display the image in the UI
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

    # Tell the UI to run this function again in 10 milliseconds
    video_label.after(10, update_frame)

# Start the video loop and open the window
update_frame()
root.mainloop()

# Clean up the camera when the window is closed
video_capture.release()