import os
import shutil
import random
from pathlib import Path

def create_1percent_dataset(source_path="facial_dataset", output_path="emotion_dataset_1percent"):
    """Create 1% subset of the emotion dataset"""
    
    source_path = Path(source_path)
    output_path = Path(output_path)
    
    # Create output structure
    for split in ['train', 'validation']:
        for emotion in ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']:
            (output_path / split / emotion).mkdir(parents=True, exist_ok=True)
    
    print("Creating 1% subset...")
    
    for split in ['train', 'validation']:
        for emotion in ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']:
            source_dir = source_path / split / emotion
            output_dir = output_path / split / emotion
            
            if source_dir.exists():
                # Get all images with multiple extensions
                images = []
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG', '*.bmp', '*.BMP']:
                    images.extend(list(source_dir.glob(ext)))
                
                print(f"Found {len(images)} images in {source_dir}")
                
                if len(images) > 0:
                    # Take 1%
                    subset_count = max(1, int(len(images) * 0.01))
                    selected = random.sample(images, min(subset_count, len(images)))
                    
                    # Copy images
                    for img in selected:
                        shutil.copy2(img, output_dir / img.name)
                    
                    print(f"{split}/{emotion}: {len(selected)}/{len(images)} images copied")
                else:
                    print(f"❌ No images found in {source_dir}")
            else:
                print(f"❌ Directory doesn't exist: {source_dir}")
    
    print(f"\n✅ 1% subset created at: {output_path}")

if __name__ == "__main__":
    random.seed(42)
    create_1percent_dataset()