import tkinter as tk
from tkinter import font, messagebox
import threading
import time
import io
import requests
from PIL import Image, ImageTk
import json
from datetime import datetime
from picamera2 import Picamera2
CAMERA_TYPE = "picamera2"

# Server URL - UPDATE THIS TO YOUR GPU SERVER IP
UNIFIED_SERVER = "http://104.171.203.124:7860"

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
        self.current_iteration = 0
        
        # Setup fonts
        self.title_font = font.Font(family="Arial", size=24, weight="bold")
        self.instruction_font = font.Font(family="Arial", size=18)
        self.button_font = font.Font(family="Arial", size=16, weight="bold")
        self.question_font = font.Font(family="Arial", size=16)
        self.status_font = font.Font(family="Arial", size=14)
        
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
            font=self.status_font,
            fg='#3498db',
            bg='#2c3e50',
            wraplength=600
        )
        self.status_label.pack(pady=(0, 10))
        
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
        
        # Progress indicator
        self.progress_label = tk.Label(
            main_frame,
            text="",
            font=self.status_font,
            fg='#f39c12',
            bg='#2c3e50'
        )
        self.progress_label.pack(pady=(0, 20))
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg='#2c3e50')
        button_frame.pack(pady=20)
        
        # Start scan button
        self.start_button = tk.Button(
            button_frame,
            text="🔍 Start Scan",
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
        
        # Reset button
        self.reset_button = tk.Button(
            button_frame,
            text="🔄 New Scan",
            font=self.button_font,
            bg='#f39c12',
            fg='white',
            activebackground='#f4d03f',
            activeforeground='white',
            padx=20,
            pady=15,
            command=self.reset_conversation,
            state=tk.DISABLED
        )
        self.reset_button.pack(side=tk.LEFT, padx=10)
        
        # Response input frame (for patient responses)
        self.response_frame = tk.Frame(main_frame, bg='#2c3e50')
        self.response_frame.pack(pady=20, fill=tk.X)
        
        self.response_label = tk.Label(
            self.response_frame,
            text="Your response:",
            font=self.instruction_font,
            fg='white',
            bg='#2c3e50'
        )
        
        # Text input with scrollbar
        text_frame = tk.Frame(self.response_frame, bg='#2c3e50')
        
        self.response_entry = tk.Text(
            text_frame,
            height=4,
            font=self.question_font,
            wrap=tk.WORD,
            bg='#ecf0f1',
            fg='#2c3e50',
            insertbackground='#2c3e50'
        )
        
        scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=self.response_entry.yview)
        self.response_entry.configure(yscrollcommand=scrollbar.set)
        
        self.response_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Submit button
        self.submit_button = tk.Button(
            self.response_frame,
            text="📤 Submit Response",
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
        
        # Bottom frame for exit and info
        bottom_frame = tk.Frame(main_frame, bg='#2c3e50')
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Connection status
        self.connection_label = tk.Label(
            bottom_frame,
            text="Checking server connection...",
            font=self.status_font,
            fg='#95a5a6',
            bg='#2c3e50'
        )
        self.connection_label.pack(side=tk.LEFT)
        
        # Exit button
        exit_button = tk.Button(
            bottom_frame,
            text="❌ Exit",
            font=self.button_font,
            bg='#e74c3c',
            fg='white',
            activebackground='#ec7063',
            activeforeground='white',
            padx=20,
            pady=10,
            command=self.exit_app
        )
        exit_button.pack(side=tk.RIGHT)
        
        # Check server connection on startup
        threading.Thread(target=self.check_server_connection, daemon=True).start()
        
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
                self.update_status("⚠️ No camera detected - Check camera connection")
                
        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            self.camera = None
            self.update_status(f"⚠️ Camera error: {str(e)}")
            
    def check_server_connection(self):
        """Check if server is reachable"""
        try:
            response = requests.get(f"{UNIFIED_SERVER}/", timeout=5)
            if response.status_code == 200:
                self.root.after(0, lambda: self.connection_label.config(
                    text="🟢 Server connected", fg='#27ae60'
                ))
            else:
                self.root.after(0, lambda: self.connection_label.config(
                    text="🟡 Server responding with errors", fg='#f39c12'
                ))
        except Exception as e:
            self.root.after(0, lambda: self.connection_label.config(
                text="🔴 Server disconnected", fg='#e74c3c'
            ))
            print(f"❌ Cannot connect to server: {e}")
            
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
            
        if not self.camera:
            messagebox.showerror("Error", "No camera available. Please check camera connection and restart.")
            return
            
        self.scanning = True
        self.start_button.config(state=tk.DISABLED)
        self.reset_button.config(state=tk.DISABLED)
        self.update_status("🔄 Preparing camera...")
        self.update_instruction("Please position your skin condition in front of the camera")
        self.update_progress("")
        
        # Start scanning in separate thread
        threading.Thread(target=self.scan_process, daemon=True).start()
        
    def scan_process(self):
        """Main scanning process - runs in separate thread"""
        try:
            # Countdown
            for i in range(3, 0, -1):
                self.update_status(f"📸 Capturing in {i}...")
                self.update_progress(f"{'●' * (4-i)}{'○' * (i-1)}")
                time.sleep(1)
                
            self.update_status("📸 Capturing image...")
            self.update_progress("●●●●")
            
            # Capture image
            image_stream = self.capture_image()
            
            self.update_status("🔍 Analyzing image with AI...")
            self.update_progress("Processing...")
            
            # Send to unified server for analysis
            files = {'image': ('image.jpg', image_stream, 'image/jpeg')}
            response = requests.post(
                f"{UNIFIED_SERVER}/analyze_frame",
                files=files,
                timeout=60  # Increased timeout for AI processing
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result['object_detected']:
                    confidence = result['detection_confidence']
                    self.update_status(f"✅ Object detected ({confidence:.1%} confidence)")
                    
                    if result['analysis']:
                        self.update_status("🩺 Starting medical consultation...")
                        # Start conversation with clinical AI
                        self.start_clinical_conversation(result['analysis'])
                    else:
                        self.update_status("❌ Medical analysis failed")
                        self.reset_ui()
                else:
                    self.update_status("❌ No object detected. Please position yourself clearly in front of camera.")
                    self.update_instruction("Make sure your skin condition is clearly visible and try again.")
                    self.reset_ui()
            else:
                error_msg = response.json().get('error', f'Server error: {response.status_code}')
                self.update_status(f"❌ Server error: {error_msg}")
                self.reset_ui()
                
        except requests.exceptions.Timeout:
            self.update_status("⏱️ Request timed out. Server may be busy.")
            self.reset_ui()
        except Exception as e:
            print(f"❌ Scan process error: {e}")
            self.update_status(f"❌ Error: {str(e)}")
            self.reset_ui()
            
    def start_clinical_conversation(self, image_analysis):
        """Start conversation with clinical AI server"""
        try:
            self.update_status("🩺 Initializing medical consultation...")
            
            # Initialize conversation
            payload = {
                "session_id": f"scan_{int(time.time())}",
                "image_analysis": image_analysis
            }
            
            response = requests.post(
                f"{UNIFIED_SERVER}/start_conversation",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                self.session_id = result['session_id']
                first_question = result['question']
                
                # Update UI to show question and response input
                self.update_status("✅ Medical consultation started")
                self.update_instruction(f"Doctor: {first_question}")
                self.update_progress("Question 1/6")
                self.current_iteration = 1
                self.show_response_input()
                self.reset_button.config(state=tk.NORMAL)
                
            else:
                error_msg = response.json().get('error', 'Unknown error')
                self.update_status(f"❌ Failed to start consultation: {error_msg}")
                self.reset_ui()
                
        except Exception as e:
            print(f"❌ Clinical conversation error: {e}")
            self.update_status(f"❌ Consultation error: {str(e)}")
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
            self.update_status("🤔 AI is thinking...")
            self.submit_button.config(state=tk.DISABLED)
            
            payload = {
                "session_id": self.session_id,
                "patient_response": response_text
            }
            
            # Continue conversation
            response = requests.post(
                f"{UNIFIED_SERVER}/continue_conversation",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('conversation_complete'):
                    # Show final diagnosis/summary
                    summary = result.get('summary', 'Consultation completed.')
                    self.update_status("✅ Consultation completed")
                    self.update_instruction(f"📋 Final Assessment:\n\n{summary}")
                    self.update_progress("Complete!")
                    self.hide_response_input()
                    
                    # Auto-reset after showing results
                    self.root.after(15000, self.reset_conversation)  # Reset after 15 seconds
                    
                else:
                    # Show next question
                    next_question = result.get('question', 'Thank you for your response.')
                    iteration = result.get('iteration', self.current_iteration + 1)
                    self.current_iteration = iteration
                    
                    self.update_instruction(f"Doctor: {next_question}")
                    self.update_progress(f"Question {iteration}/6")
                    self.response_entry.delete("1.0", tk.END)
                    
                self.update_status("💬 Ready for your response")
                self.submit_button.config(state=tk.NORMAL)
                
            else:
                error_msg = response.json().get('error', 'Unknown error')
                self.update_status(f"❌ Failed to process response: {error_msg}")
                self.submit_button.config(state=tk.NORMAL)
                
        except requests.exceptions.Timeout:
            self.update_status("⏱️ Response timed out. AI may be busy.")
            self.submit_button.config(state=tk.NORMAL)
        except Exception as e:
            print(f"❌ Response submission error: {e}")
            self.update_status(f"❌ Error: {str(e)}")
            self.submit_button.config(state=tk.NORMAL)
            
    def show_response_input(self):
        """Show response input widgets"""
        self.response_label.pack(pady=(20, 5))
        text_frame = self.response_entry.master
        text_frame.pack(fill=tk.X, pady=5)
        self.submit_button.pack(pady=10)
        
        # Focus on text input
        self.response_entry.focus_set()
        
    def hide_response_input(self):
        """Hide response input widgets"""
        self.response_label.pack_forget()
        text_frame = self.response_entry.master
        text_frame.pack_forget()
        self.submit_button.pack_forget()
        
    def reset_conversation(self):
        """Reset to start a new conversation"""
        self.session_id = None
        self.current_iteration = 0
        self.conversation_history = []
        self.scanning = False
        self.reset_ui(delay=0)
        
    def reset_ui(self, delay=3):
        """Reset UI to initial state"""
        def reset():
            if delay > 0:
                time.sleep(delay)
            self.scanning = False
            self.root.after(0, self._reset_ui_main_thread)
            
        if delay > 0:
            threading.Thread(target=reset, daemon=True).start()
        else:
            self._reset_ui_main_thread()
            
    def _reset_ui_main_thread(self):
        """Reset UI components (must run in main thread)"""
        self.start_button.config(state=tk.NORMAL)
        self.reset_button.config(state=tk.DISABLED)
        self.submit_button.config(state=tk.NORMAL)
        self.update_status("Ready to scan")
        self.update_instruction("Touch 'Start Scan' to begin analyzing your skin condition")
        self.update_progress("")
        self.hide_response_input()
        
    def update_status(self, text):
        """Update status label (thread-safe)"""
        self.root.after(0, lambda: self.status_label.config(text=text))
        
    def update_instruction(self, text):
        """Update instruction label (thread-safe)"""
        self.root.after(0, lambda: self.instruction_label.config(text=text))
        
    def update_progress(self, text):
        """Update progress label (thread-safe)"""
        self.root.after(0, lambda: self.progress_label.config(text=text))
        
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
    
    # Bind escape key to exit (for testing without touchscreen)
    root.bind('<Escape>', lambda e: app.exit_app())
    
    # Bind Enter key to submit response when text widget has focus
    def on_enter(event):
        if app.submit_button['state'] == tk.NORMAL and app.response_entry.winfo_viewable():
            app.submit_response()
            return 'break'
    
    root.bind('<Control-Return>', on_enter)  # Ctrl+Enter to submit
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.exit_app()

if __name__ == "__main__":
    # Configuration check
    if "YOUR_GPU_SERVER_IP" in UNIFIED_SERVER:
        print("⚠️  WARNING: Please update UNIFIED_SERVER with your actual GPU server IP!")
        print(f"Current setting: {UNIFIED_SERVER}")
        print("Example: UNIFIED_SERVER = 'http://192.168.1.100:7860'")
        print("")
    
    print("🚀 Medical Skin Scanner - Raspberry Pi Client")
    print(f"📡 Server: {UNIFIED_SERVER}")
    print(f"📷 Camera: {CAMERA_TYPE if CAMERA_TYPE else 'Not available'}")
    print("🖥️  Starting touchscreen interface...")
    print("")
    
    main()