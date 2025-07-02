import tkinter as tk
from tkinter import font, messagebox
import threading
import time
import io
import requests
from PIL import Image, ImageTk
import json
from datetime import datetime

# Try importing the appropriate camera library
try:
    # For newer Raspberry Pi OS with libcamera
    from picamera2 import Picamera2
    CAMERA_TYPE = "picamera2"
    print("✅ Using picamera2")
except ImportError:
    try:
        # For older Raspberry Pi OS
        import picamera
        CAMERA_TYPE = "picamera"
        print("✅ Using picamera (legacy)")
    except ImportError:
        print("❌ No camera library found! Install picamera2 or picamera")
        CAMERA_TYPE = None

# Server URL - UPDATE THIS TO YOUR GPU SERVER IP
UNIFIED_SERVER = "http://YOUR_GPU_SERVER_IP:7860"

class MedicalScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Medical Skin Scanner")
        self.root.attributes('-fullscreen', True)  # Fullscreen for touchscreen
        self.root.configure(bg='#2c3e50')
        
        # State variables
        self.scanning = False
        self.session_id = None
        self.conversation_history = []
        self.camera = None
        
        # Setup fonts
        self.title_font = font.Font(family="Arial", size=24, weight="bold")
        self.instruction_font = font.Font(family="Arial", size=18)
        self.button_font = font.Font(family="Arial", size=16, weight="bold")
        self.question_font = font.Font(family="Arial", size=16)
        
        self.setup_ui()
        self.initialize_camera()
        
    def setup_ui(self):
        """Setup the touchscreen interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        self.title_label = tk.Label(
            main_frame,
            text="🏥 Medical Skin Scanner",
            font=self.title_font,
            fg='white',
            bg='#2c3e50'
        )
        self.title_label.pack(pady=(0, 20))
        
        # Status display
        self.status_label = tk.Label(
            main_frame,
            text="Ready to scan",
            font=self.instruction_font,
            fg='#3498db',
            bg='#2c3e50',
            wraplength=600
        )
        self.status_label.pack(pady=(0, 20))
        
        # Main instruction/question display
        self.instruction_label = tk.Label(
            main_frame,
            text="Touch 'Start Scan' to begin analyzing your skin condition",
            font=self.question_font,
            fg='white',
            bg='#2c3e50',
            wraplength=700,
            justify=tk.CENTER
        )
        self.instruction_label.pack(pady=(0, 30))
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg='#2c3e50')
        button_frame.pack(pady=20)
        
        # Start scan button
        self.start_button = tk.Button(
            button_frame,
            text="Start Scan",
            font=self.button_font,
            bg='#27ae60',
            fg='white',
            activebackground='#2ecc71',
            activeforeground='white',
            padx=30,
            pady=15,
            command=self.start_scan
        )
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        # Response input (for patient responses)
        self.response_frame = tk.Frame(main_frame, bg='#2c3e50')
        self.response_frame.pack(pady=20, fill=tk.X)
        
        self.response_label = tk.Label(
            self.response_frame,
            text="Your response:",
            font=self.instruction_font,
            fg='white',
            bg='#2c3e50'
        )
        
        self.response_entry = tk.Text(
            self.response_frame,
            height=3,
            font=self.question_font,
            wrap=tk.WORD
        )
        
        self.submit_button = tk.Button(
            self.response_frame,
            text="Submit Response",
            font=self.button_font,
            bg='#3498db',
            fg='white',
            activebackground='#5dade2',
            activeforeground='white',
            padx=20,
            pady=10,
            command=self.submit_response
        )
        
        # Initially hide response widgets
        self.hide_response_input()
        
        # Exit button
        exit_button = tk.Button(
            main_frame,
            text="Exit",
            font=self.button_font,
            bg='#e74c3c',
            fg='white',
            activebackground='#ec7063',
            activeforeground='white',
            padx=20,
            pady=10,
            command=self.exit_app
        )
        exit_button.pack(side=tk.BOTTOM, pady=10)
        
    def initialize_camera(self):
        """Initialize the camera based on available library"""
        try:
            if CAMERA_TYPE == "picamera2":
                self.camera = Picamera2()
                # Configure camera for still capture
                config = self.camera.create_still_configuration(
                    main={"size": (640, 480)}
                )
                self.camera.configure(config)
                print("✅ Camera initialized with picamera2")
                
            elif CAMERA_TYPE == "picamera":
                self.camera = picamera.PiCamera()
                self.camera.resolution = (640, 480)
                print("✅ Camera initialized with picamera")
                
            else:
                print("❌ No camera available")
                self.camera = None
                
        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            self.camera = None
            
    def capture_image(self):
        """Capture image using appropriate camera library"""
        if not self.camera:
            raise Exception("No camera available")
            
        try:
            stream = io.BytesIO()
            
            if CAMERA_TYPE == "picamera2":
                # Start camera if not already started
                if not self.camera.started:
                    self.camera.start()
                    time.sleep(2)  # Let camera warm up
                
                # Capture to stream
                self.camera.capture_file(stream, format='jpeg')
                
            elif CAMERA_TYPE == "picamera":
                # Start preview and capture
                self.camera.start_preview()
                time.sleep(2)  # Camera warm-up time
                self.camera.capture(stream, format='jpeg')
                self.camera.stop_preview()
                
            stream.seek(0)
            return stream
            
        except Exception as e:
            print(f"❌ Image capture failed: {e}")
            raise
            
    def start_scan(self):
        """Start the scanning process"""
        if self.scanning:
            return
            
        self.scanning = True
        self.start_button.config(state=tk.DISABLED)
        self.update_status("Preparing camera...")
        self.update_instruction("Please position your skin condition in front of the camera")
        
        # Start scanning in separate thread
        threading.Thread(target=self.scan_process, daemon=True).start()
        
    def scan_process(self):
        """Main scanning process - runs in separate thread"""
        try:
            # Countdown
            for i in range(3, 0, -1):
                self.update_status(f"Scanning in {i}...")
                time.sleep(1)
                
            self.update_status("Capturing image...")
            
            # Capture image
            image_stream = self.capture_image()
            
            self.update_status("Analyzing image...")
            
            # Send to unified server for analysis
            files = {'image': ('image.jpg', image_stream, 'image/jpeg')}
            response = requests.post(
                f"{UNIFIED_SERVER}/analyze_frame",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result['object_detected']:
                    self.update_status("Object detected! Processing medical analysis...")
                    
                    if result['analysis']:
                        # Start conversation with clinical AI
                        self.start_clinical_conversation(result['analysis'])
                    else:
                        self.update_status("Analysis failed")
                        self.reset_ui()
                else:
                    self.update_status("No object detected. Please try again.")
                    self.reset_ui()
            else:
                self.update_status(f"Server error: {response.status_code}")
                self.reset_ui()
                
        except Exception as e:
            print(f"❌ Scan process error: {e}")
            self.update_status(f"Error: {str(e)}")
            self.reset_ui()
            
    def start_clinical_conversation(self, image_analysis):
        """Start conversation with clinical AI server"""
        try:
            self.update_status("Starting medical consultation...")
            
            # Initialize conversation
            payload = {
                "session_id": f"scan_{int(time.time())}",
                "image_analysis": image_analysis
            }
            
            response = requests.post(
                f"{UNIFIED_SERVER}/start_conversation",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.session_id = result['session_id']
                first_question = result['question']
                
                # Update UI to show question and response input
                self.update_status("Medical consultation started")
                self.update_instruction(first_question)
                self.show_response_input()
                
            else:
                self.update_status("Failed to start consultation")
                self.reset_ui()
                
        except Exception as e:
            print(f"❌ Clinical conversation error: {e}")
            self.update_status(f"Consultation error: {str(e)}")
            self.reset_ui()
            
    def submit_response(self):
        """Submit patient response to clinical AI"""
        response_text = self.response_entry.get("1.0", tk.END).strip()
        
        if not response_text:
            messagebox.showwarning("Warning", "Please enter a response")
            return
            
        if not self.session_id:
            messagebox.showerror("Error", "No active session")
            return
            
        try:
            self.update_status("Processing your response...")
            self.submit_button.config(state=tk.DISABLED)
            
            payload = {
                "session_id": self.session_id,
                "patient_response": response_text
            }
            
            # This endpoint would need to be implemented in the clinical server
            response = requests.post(
                f"{UNIFIED_SERVER}/continue_conversation",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('conversation_complete'):
                    # Show final diagnosis/summary
                    self.update_instruction(f"Consultation complete.\n\n{result.get('summary', '')}")
                    self.hide_response_input()
                    self.reset_ui(delay=10)
                else:
                    # Show next question
                    next_question = result.get('question', 'Thank you for your response.')
                    self.update_instruction(next_question)
                    self.response_entry.delete("1.0", tk.END)
                    
                self.update_status("Ready for your response")
                self.submit_button.config(state=tk.NORMAL)
                
            else:
                self.update_status("Failed to process response")
                self.submit_button.config(state=tk.NORMAL)
                
        except Exception as e:
            print(f"❌ Response submission error: {e}")
            self.update_status(f"Error: {str(e)}")
            self.submit_button.config(state=tk.NORMAL)
            
    def show_response_input(self):
        """Show response input widgets"""
        self.response_label.pack(pady=(10, 5))
        self.response_entry.pack(fill=tk.X, pady=5)
        self.submit_button.pack(pady=10)
        
    def hide_response_input(self):
        """Hide response input widgets"""
        self.response_label.pack_forget()
        self.response_entry.pack_forget()
        self.submit_button.pack_forget()
        
    def reset_ui(self, delay=3):
        """Reset UI to initial state"""
        def reset():
            if delay > 0:
                time.sleep(delay)
            self.scanning = False
            self.session_id = None
            self.root.after(0, self._reset_ui_main_thread)
            
        if delay > 0:
            threading.Thread(target=reset, daemon=True).start()
        else:
            self._reset_ui_main_thread()
            
    def _reset_ui_main_thread(self):
        """Reset UI components (must run in main thread)"""
        self.start_button.config(state=tk.NORMAL)
        self.update_status("Ready to scan")
        self.update_instruction("Touch 'Start Scan' to begin analyzing your skin condition")
        self.hide_response_input()
        
    def update_status(self, text):
        """Update status label (thread-safe)"""
        self.root.after(0, lambda: self.status_label.config(text=text))
        
    def update_instruction(self, text):
        """Update instruction label (thread-safe)"""
        self.root.after(0, lambda: self.instruction_label.config(text=text))
        
    def exit_app(self):
        """Clean up and exit"""
        try:
            if self.camera and CAMERA_TYPE == "picamera2":
                if self.camera.started:
                    self.camera.stop()
                self.camera.close()
            elif self.camera and CAMERA_TYPE == "picamera":
                self.camera.close()
        except:
            pass
        
        self.root.quit()
        self.root.destroy()

def main():
    # Check server connectivity
    print("🔍 Checking server connectivity...")
    
    try:
        response = requests.get(f"{UNIFIED_SERVER}/", timeout=5)
        print("✅ Unified medical server connected")
    except:
        print(f"❌ Cannot connect to unified server at {UNIFIED_SERVER}")
        print("Please update UNIFIED_SERVER variable with correct IP")
    
    # Create and run app
    root = tk.Tk()
    app = MedicalScannerApp(root)
    
    # Bind escape key to exit (for testing)
    root.bind('<Escape>', lambda e: app.exit_app())
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.exit_app()

if __name__ == "__main__":
    main()