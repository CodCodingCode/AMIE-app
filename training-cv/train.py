from ultralytics import YOLO
import cv2
import os
import yaml
from pathlib import Path
import shutil

def convert_to_yolo_format(source_path="emotion_dataset_1percent"):
    """Convert emotion dataset to YOLO format"""
    
    source_path = Path(source_path)
    yolo_path = Path(f"{source_path.name}_yolo")
    
    # Create YOLO structure
    for split in ['train', 'val']:
        (yolo_path / split / 'images').mkdir(parents=True, exist_ok=True)
        (yolo_path / split / 'labels').mkdir(parents=True, exist_ok=True)
    
    emotion_classes = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
    
    print("Converting to YOLO format...")
    
    for split in ['train', 'validation']:
        yolo_split = 'train' if split == 'train' else 'val'
        
        for class_idx, emotion in enumerate(emotion_classes):
            emotion_dir = source_path / split / emotion
            
            if emotion_dir.exists():
                for img_file in emotion_dir.glob("*.jpg"):
                    # Copy image
                    new_name = f"{emotion}_{img_file.stem}.jpg"
                    shutil.copy2(img_file, yolo_path / yolo_split / 'images' / new_name)
                    
                    # Create label (whole image is the face/emotion)
                    label_content = f"{class_idx} 0.5 0.5 1.0 1.0\n"
                    label_file = yolo_path / yolo_split / 'labels' / f"{emotion}_{img_file.stem}.txt"
                    
                    with open(label_file, 'w') as f:
                        f.write(label_content)
                
                print(f"Processed {emotion}: {len(list(emotion_dir.glob('*.jpg')))} images")
    
    # Create dataset.yaml
    dataset_config = {
        'path': str(yolo_path.absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'nc': len(emotion_classes),
        'names': emotion_classes
    }
    
    with open(yolo_path / 'dataset.yaml', 'w') as f:
        yaml.dump(dataset_config, f)
    
    print(f"✅ YOLO dataset created: {yolo_path}")
    return yolo_path / 'dataset.yaml'

def train_emotion_model():
    """Train YOLOv8 for emotion detection"""
    
    # Convert dataset
    dataset_yaml = convert_to_yolo_format()
    
    # Load YOLOv8 model (nano for speed)
    model = YOLO('yolov8n.pt')
    
    print("Starting training...")
    print("⏱️ Estimated time: 20-40 minutes on CPU, 5-15 minutes on GPU")
    
    # Train model
    results = model.train(
        data=str(dataset_yaml),
        epochs=50,
        imgsz=416,          # Smaller for speed
        batch=8,            # Small batch for CPU
        name='emotion_1percent',
        patience=10,
        device='cpu',       # Change to 0 for GPU
        
        # Optimization
        cache=False,        # Don't cache on CPU
        save=True,
        
        # Augmentation
        flipud=0.0,         # No vertical flip for faces
        fliplr=0.5,         # Horizontal flip only
        mosaic=0.5,
        
        # Learning
        lr0=0.01,
        momentum=0.937,
        weight_decay=0.0005,
    )
    
    model_path = "runs/detect/emotion_1percent/weights/best.pt"
    print(f"✅ Training complete! Model saved: {model_path}")
    return model_path

def test_trained_model(model_path="runs/detect/emotion_1percent/weights/best.pt"):
    """Test the trained model on webcam"""
    
    model = YOLO(model_path)
    cap = cv2.VideoCapture(0)
    
    emotion_colors = {
        0: (0, 0, 255),      # angry - red
        1: (0, 255, 0),      # disgust - green
        2: (128, 0, 128),    # fear - purple
        3: (0, 255, 255),    # happy - yellow
        4: (128, 128, 128),  # neutral - gray
        5: (255, 0, 0),      # sad - blue
        6: (255, 165, 0)     # surprise - orange
    }
    
    emotion_names = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
    
    print("Testing model on webcam. Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Run detection
        results = model(frame, conf=0.3)
        
        # Draw results
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = box.conf[0]
                    cls = int(box.cls[0])
                    
                    color = emotion_colors.get(cls, (255, 255, 255))
                    emotion = emotion_names[cls]
                    
                    # Draw box and label
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    label = f"{emotion}: {conf:.2f}"
                    cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        cv2.imshow('Emotion Detection Test', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    print("🚀 YOLOv8 Emotion Detection Training")
    print("=====================================")
    
    # Check if 1% dataset exists
    if not Path("emotion_dataset_1percent").exists():
        print("❌ Run the subset creation script first!")
        print("   python create_subset.py")
        exit()
    
    # Step 1: Train model
    print("\n1. Training YOLOv8 model...")
    model_path = train_emotion_model()
    
    # Step 2: Test model
    print("\n2. Testing trained model...")
    test_trained_model(model_path)
    
    print("\n🎉 Training complete!")
    print(f"📁 Model saved at: {model_path}")
    print("\nNext steps:")
    print("- If results look good, train on full dataset")
    print("- Adjust hyperparameters if needed")
    print("- Export model for deployment")