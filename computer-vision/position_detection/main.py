import cv2
import torch

# Load pre-trained YOLOv5 model (person detection)
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

# Store last detection results
last_detections = []
frame_count = 0

def run_detection(frame):
    """Run object detection and return results"""
    results = model(frame)
    persons = results.xyxy[0]  # bounding boxes for detected persons
    
    detections = []
    for *box, conf, cls in persons:
        if int(cls) == 0 and conf > 0.5:  # class 0 = person in COCO
            x1, y1, x2, y2 = map(int, box)
            box_height = y2 - y1
            detections.append((x1, y1, x2, y2, box_height))
    
    return detections

def draw_results(frame, detections, min_box_height=400, max_box_height=800):
    """Draw bounding boxes and distance feedback using cached detection results"""
    for x1, y1, x2, y2, box_height in detections:
        # Draw box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

        # Check distance based on box size
        if box_height > max_box_height:
            cv2.putText(frame, "TOO CLOSE - Step Back", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        elif box_height < min_box_height:
            cv2.putText(frame, "TOO FAR - Step Closer", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        else:
            cv2.putText(frame, "GOOD DISTANCE", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    return frame

# Initialize camera
cap = cv2.VideoCapture(0)

print("Press 'q' to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't read camera")
        break
    
    # Flip frame so it's like a mirror
    frame = cv2.flip(frame, 1)
    
    frame_count += 1
    
    # Only run detection every 10 frames (or whatever number works for you)
    if frame_count % 10 == 0:
        last_detections = run_detection(frame.copy())
    
    # Always draw results using the most recent detection data
    frame = draw_results(frame, last_detections)
    
    # Show the frame
    cv2.imshow('Distance Check', frame)
    
    # Quit if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
cv2.destroyAllWindows()