# AI-Attendance-Tracker

A visual-based attendance tracker that uses computer vision to recognize students and mark them present or absent.

## Features
- Real-time face recognition through a webcam
- Live class roster dashboard (Tkinter)
- Automatic daily CSV attendance log
- Shows "Not Recognized" for unknown faces
- Requires several consecutive matching frames before marking someone present

## Requirements
- Python 3.8+
- A webcam

## Installation
```bash
git clone https://github.com/Mackaaw/AI-Attendance-Tracker.git
cd AI-Attendance-Tracker
pip install -r requirements.txt
```

Note: `face_recognition` depends on `dlib`, which can be tricky to install on Windows. See the [face_recognition installation guide](https://github.com/ageitgey/face_recognition) if you run into problems.

## Setup
1. Create a folder named `students` next to `attendance_system.py`.
2. Add one clear, front-facing photo per student, named after the student (e.g. `john.jpg`).

## Usage
```bash
python attendance_system.py
```

The attendance log is saved as `Attendance_YYYY-MM-DD.csv`.

## Limitations
Face recognition accuracy depends on lighting, camera quality, and the photos provided. Thresholds can be tuned in the script (`TOLERANCE`, `MARGIN`, `CONFIRM_FRAMES`).
