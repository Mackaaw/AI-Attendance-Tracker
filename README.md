# AI-Attendance-Tracker

A visual-based attendance tracker that uses computer vision to recognize students and mark them as present or absent.

## Features
- Real-time face recognition through a webcam
- Live class roster dashboard (Tkinter)
- Automatic daily CSV attendance log
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
2. Add one clear, front-facing photo per student, named after the student (e.g. `john.jpg`). Make sure the lighting is clear.

## Custom Sound
The app plays `success.wav` (included in the repo) when a student is marked present.
- To use your own sound, replace `success.wav` with another file of the same name.
- It must be a real **WAV** file (16-bit PCM). Renaming an mp3 or mp4 to `.wav` will not work.
- Sound playback uses `winsound`, so it works on **Windows**. On other systems the app falls back to a basic system beep.

## Usage
```bash
python attendance_system.py
```

The attendance log is saved as an excel file `Attendance_YYYY-MM-DD.csv`.

## Limitations
Face recognition accuracy depends on lighting, camera quality, and the photos provided. Thresholds can be tuned in the script (`TOLERANCE`, `MARGIN`, `CONFIRM_FRAMES`).

This project was made as an AI CAPSTONE PROJECT by a team of 5 for my school project, aligned with United Nations SDG 4 - Quality Education
-------------------------------------------------------------------------------------------------------------------------------------------------------------
