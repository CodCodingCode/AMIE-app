import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import os
from ultralytics import YOLO
import urllib.request
from pyVHR.signals import Signal
from pyVHR.vhr import HRVideo

# ============================
# Download YOLO Face Model if not exists
# ============================
model_url = "https://github.com/lindevs/yolov8-face/releases/latest/download/yolov8n-face-lindevs.pt"
model_path = "yolov8n-face-lindevs.pt"

if not os.path.isfile(model_path):
    print("Downloading YOLO face model...")
    urllib.request.urlretrieve(model_url, model_path)
    print("Download complete.")

# ============================
# Initialize Video Capture and YOLO
# ============================
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

model = YOLO(model_path)

# ============================
# Parameters
# ============================
frame_rate = 30
buffer_size = frame_rate * 10  # 10-second window
signal_data = []

plt.ion()
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
ax.set_ylim(-10, 10)
ax.set_xlim(0, buffer_size)
ax.set_title('Live Respiratory Signal (pyVHR)')
ax.set_xlabel('Frames')
ax.set_ylabel('Amplitude')

# Initialize pyVHR signal processor
vhr = HRVideo()

# ============================
# Main Loop
# ============================
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        small_frame = cv2.resize(frame, (640, 480))

        results = model.predict(small_frame, verbose=False)

        if results and results[0].boxes:
            box = results[0].boxes.xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = box

            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(small_frame.shape[1], x2), min(small_frame.shape[0], y2)

            roi = small_frame[y1:y2, x1:x2]

            if roi.size > 0:
                mean_green = np.mean(roi[:, :, 1])
                signal_data.append(mean_green)

                if len(signal_data) > buffer_size:
                    signal_data = signal_data[-buffer_size:]

                # Use pyVHR signal processing (placeholder for actual RR estimation)
                sig = Signal(signal_data, frame_rate)
                processed_signal = sig.signal - np.mean(sig.signal)

                line.set_ydata(processed_signal)
                line.set_xdata(np.arange(len(processed_signal)))
                ax.set_xlim(0, len(processed_signal))
                ax.set_ylim(-np.std(processed_signal)*3, np.std(processed_signal)*3)
                fig.canvas.draw()
                fig.canvas.flush_events()

                cv2.rectangle(small_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.imshow('rPPG Face Detection', small_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    pass

cap.release()
cv2.destroyAllWindows()
plt.ioff()
plt.show()
