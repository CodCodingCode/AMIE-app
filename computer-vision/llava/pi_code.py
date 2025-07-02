import io
import requests
import picamera

# Backend URL (Update this to your server’s IP or domain)
BACKEND_URL = "http://104.171.203.124:7860/analyze_image"

# Optional: Custom prompt
payload = {
    'prompt': 'Describe this medical image clearly.'
}

# Capture image to memory
stream = io.BytesIO()
with picamera.PiCamera() as camera:
    camera.resolution = (640, 480)
    camera.start_preview()
    camera.capture(stream, format='jpeg')
    camera.close()

# Prepare stream for upload
stream.seek(0)
files = {'image': ('image.jpg', stream, 'image/jpeg')}

# Send POST request
print("📤 Sending image to backend...")
response = requests.post(BACKEND_URL, files=files, data=payload)

# Output result
if response.status_code == 200:
    print("✅ Response from backend:")
    print(response.json())
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
