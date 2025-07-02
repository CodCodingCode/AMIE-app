import cv2
import anthropic
import base64
import os
from datetime import datetime
from prompts.skin_prompt import skin_prompt
import os

# Initialize client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def analyze_skin_condition(image_path):
    # Read and encode image
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Send to Claude
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": skin_prompt
                    }
                ]
            }
        ]
    )
    
    return message.content[0].text

def main():
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    # Create images directory if it doesn't exist
    os.makedirs("computer-vision/claude/images", exist_ok=True)
    
    print("Camera started. Press 't' to take picture and analyze, 'q' to quit")
    
    while True:
        # Read frame from camera
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Could not read frame")
            break
        
        # Display the frame
        cv2.imshow('Camera Feed - Press "t" to capture', frame)
        
        # Check for key press
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('t'):
            # Generate timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = f"computer-vision/claude/images/capture_{timestamp}.png"
            
            # Save the frame
            cv2.imwrite(image_path, frame)
            print(f"\nImage captured: {image_path}")
            print("Analyzing skin condition...")
            
            try:
                # Analyze the captured image
                result = analyze_skin_condition(image_path)
                print("\n" + "="*50)
                print("SKIN ANALYSIS RESULT:")
                print("="*50)
                print(result)
                print("="*50 + "\n")
            except Exception as e:
                print(f"Error analyzing image: {e}")
        
        elif key == ord('q'):
            break
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()