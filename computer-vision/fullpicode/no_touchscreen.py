#!/usr/bin/env python3
"""
Complete Live Medical Scanner for Raspberry Pi
Uses quick detection endpoint and complete analysis pipeline
"""

import io
import requests
import time
import cv2
import numpy as np
from datetime import datetime
from picamera2 import Picamera2
import threading

# Configuration
GPU_SERVER_URL = "http://192.222.58.119:7860"
DETECTION_INTERVAL = 3  # Check for detection every 3 seconds
ANALYSIS_COOLDOWN = 10  # Wait 10 seconds between full analyses
DETECTION_CONFIDENCE = 0.4  # Minimum confidence for triggering analysis

class CompleteLiveScanner:
    def __init__(self):
        self.camera = None
        self.running = False
        self.last_analysis_time = 0
        self.processing = False
        
        self.initialize_camera()
        
    def initialize_camera(self):
        """Initialize camera for live monitoring"""
        try:
            self.camera = Picamera2()
            
            # Configure for live preview
            config = self.camera.create_preview_configuration(
                main={"size": (640, 480)}
            )
            self.camera.configure(config)
            
            print("✅ Camera initialized for live detection")
        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            self.camera = None
            
    def check_server(self):
        """Check if GPU server is accessible"""
        try:
            response = requests.get(f"{GPU_SERVER_URL}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ GPU server online - Models loaded: {data.get('models_loaded', 'Unknown')}")
                return True
            return False
        except Exception as e:
            print(f"❌ GPU server check failed: {e}")
            return False
            
    def capture_detection_frame(self):
        """Capture low-res frame for detection check"""
        try:
            stream = io.BytesIO()
            self.camera.capture_file(stream, format='jpeg')
            stream.seek(0)
            return stream.getvalue()
        except Exception as e:
            print(f"❌ Detection frame capture failed: {e}")
            return None
            
    def capture_analysis_frame(self):
        """Capture high-res frame for full analysis"""
        try:
            print("📸 Capturing high-resolution image for complete analysis...")
            
            # Switch to still configuration temporarily
            self.camera.stop()
            
            still_config = self.camera.create_still_configuration(
                main={"size": (1024, 768)}
            )
            self.camera.configure(still_config)
            self.camera.start()
            time.sleep(1)  # Longer stabilization for better image
            
            # Capture high-res image
            stream = io.BytesIO()
            self.camera.capture_file(stream, format='jpeg')
            stream.seek(0)
            image_bytes = stream.getvalue()
            
            # Return to preview mode
            self.camera.stop()
            preview_config = self.camera.create_preview_configuration(
                main={"size": (640, 480)}
            )
            self.camera.configure(preview_config)
            self.camera.start()
            
            print(f"✅ Captured {len(image_bytes)} bytes for analysis")
            return image_bytes
            
        except Exception as e:
            print(f"❌ Analysis frame capture failed: {e}")
            return None
            
    def quick_detection_check(self, image_bytes):
        """Send frame to GPU server for quick YOLO detection only"""
        try:
            files = {'image': ('check.jpg', image_bytes, 'image/jpeg')}
            
            # Use quick detection endpoint with short timeout
            response = requests.post(
                f"{GPU_SERVER_URL}/quick_detect",
                files=files,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('detected', False):
                    detection = result.get('detection', {})
                    if detection.get('confidence', 0) >= DETECTION_CONFIDENCE:
                        return detection
            return None
                
        except requests.exceptions.Timeout:
            print("⏱️ Quick detection timed out")
            return None
        except Exception as e:
            print(f"❌ Quick detection failed: {e}")
            return None
            
    def run_complete_analysis(self, image_bytes):
        """Send high-res image for complete medical analysis pipeline"""
        try:
            print("🚀 Running COMPLETE medical analysis pipeline...")
            
            files = {'image': ('analysis.jpg', image_bytes, 'image/jpeg')}
            response = requests.post(
                f"{GPU_SERVER_URL}/analyze_frame",
                files=files,
                timeout=300  # 5 minutes for complete pipeline
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result
                else:
                    print(f"❌ Pipeline failed: {result.get('error')}")
                    return None
            else:
                print(f"❌ Server error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("⏱️ Complete analysis timed out (this is normal for LLaVA)")
            return None
        except Exception as e:
            print(f"❌ Complete analysis failed: {e}")
            return None
            
    def display_results(self, result):
        """Display complete medical analysis results"""
        print("\n" + "=" * 80)
        print("🎉 AUTOMATIC MEDICAL ANALYSIS COMPLETE!")
        print("=" * 80)
        
        # Detection info
        detection = result['detection']
        print(f"\n🎯 Auto-detected: {detection['class']} ({detection['confidence']:.1%} confidence)")
        
        # LLaVA analysis
        print(f"\n👁️ LLaVA Visual Analysis:")
        print("─" * 50)
        print(result['llava_analysis'])
        
        # Combined patient info
        print(f"\n📋 Combined Patient Information:")
        print("─" * 50)
        print(result['combined_patient_info'])
        
        # Clinical summary
        print(f"\n🩺 Clinical Summary:")
        print("─" * 50)
        print(result['clinical_summary'])
        
        # Diagnostic analysis  
        print(f"\n🔬 Diagnostic Analysis:")
        print("─" * 50)
        print(result['diagnostic_analysis'])
        
        # Final medical question
        print(f"\n" + "=" * 80)
        print("❓ FINAL MEDICAL QUESTION")
        print("=" * 80)
        print(f"🩺 {result['medical_question']}")
        print("=" * 80)
        
        # Save timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n⏰ Analysis completed at: {timestamp}")
        print(f"👁️ Resuming live detection in {ANALYSIS_COOLDOWN} seconds...\n")
        
    def process_detection(self, detection):
        """Process detected object (runs in separate thread)"""
        try:
            print(f"\n🎯 PROCESSING: {detection['class']} ({detection['confidence']:.1%} confidence)")
            print("🔄 Starting complete medical analysis pipeline...")
            
            # Capture high-resolution image
            image_bytes = self.capture_analysis_frame()
            if not image_bytes:
                print("❌ Failed to capture analysis image")
                return
                
            # Run complete analysis pipeline
            result = self.run_complete_analysis(image_bytes)
            if result:
                self.display_results(result)
            else:
                print(f"\n❌ Complete analysis failed! Resuming detection...\n")
                
        except Exception as e:
            print(f"❌ Processing error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Reset processing flag
            self.processing = False
            
    def live_detection_loop(self):
        """Main live detection loop"""
        print("\n🔴 LIVE MEDICAL DETECTION ACTIVE")
        print("=" * 50)
        print("👁️ Camera continuously monitoring for person/hand...")
        print("🎯 Will auto-capture and analyze when detected")
        print(f"⚡ Using quick detection checks every {DETECTION_INTERVAL}s")
        print(f"🕐 Analysis cooldown: {ANALYSIS_COOLDOWN}s between analyses")
        print("Press Ctrl+C to quit\n")
        
        detection_count = 0
        
        while self.running:
            try:
                current_time = time.time()
                detection_count += 1
                
                # Status update
                status = f"👀 Monitoring... ({detection_count}) - Press Ctrl+C to quit"
                if self.processing:
                    status = "🔄 Processing analysis... - Press Ctrl+C to quit"
                print(status, end='\r')
                
                # Skip detection if currently processing
                if self.processing:
                    time.sleep(1)
                    continue
                
                # Capture frame for detection
                frame_bytes = self.capture_detection_frame()
                if not frame_bytes:
                    time.sleep(1)
                    continue
                
                # Quick detection check with GPU server
                detection = self.quick_detection_check(frame_bytes)
                
                if detection:
                    # Check cooldown period
                    if current_time - self.last_analysis_time > ANALYSIS_COOLDOWN:
                        print(f"\n🎯 DETECTED: {detection['class']} ({detection['confidence']:.1%})")
                        print("🚀 Triggering complete medical analysis...")
                        
                        # Set processing flag and timestamp
                        self.processing = True
                        self.last_analysis_time = current_time
                        
                        # Process in separate thread
                        analysis_thread = threading.Thread(
                            target=self.process_detection,
                            args=(detection,)
                        )
                        analysis_thread.start()
                    else:
                        remaining = ANALYSIS_COOLDOWN - (current_time - self.last_analysis_time)
                        print(f"\n🕐 Detection on cooldown ({remaining:.1f}s remaining)")
                
                # Wait before next detection check
                time.sleep(DETECTION_INTERVAL)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n❌ Detection loop error: {e}")
                time.sleep(3)
                
        print("\n🛑 Live detection stopped")
        
    def start_live_detection(self):
        """Start the live detection system"""
        if not self.camera:
            print("❌ No camera available")
            return False
            
        if not self.check_server():
            print("❌ GPU server not accessible")
            return False
            
        try:
            # Start camera
            self.camera.start()
            print("📷 Camera warming up...")
            time.sleep(3)
            
            self.running = True
            
            # Start detection loop
            self.live_detection_loop()
            
            return True
            
        except Exception as e:
            print(f"❌ Live detection failed: {e}")
            return False
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources"""
        try:
            self.running = False
            if self.camera:
                self.camera.stop()
                self.camera.close()
                print("📷 Camera closed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

def main():
    print("🏥 Complete Live Medical Detection Scanner")
    print("=" * 60)
    print(f"🌐 GPU Server: {GPU_SERVER_URL}")
    print("📋 Pipeline: Quick Detect → Capture → Complete Analysis → Question")
    print(f"🎯 Detection Confidence: {DETECTION_CONFIDENCE}")
    print(f"⏱️ Detection Interval: {DETECTION_INTERVAL}s")
    print(f"🕐 Analysis Cooldown: {ANALYSIS_COOLDOWN}s")
    
    scanner = CompleteLiveScanner()
    
    try:
        print("\n🚀 Starting live medical detection...")
        success = scanner.start_live_detection()
        
        if not success:
            print("❌ Failed to start live detection")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    finally:
        scanner.cleanup()

if __name__ == "__main__":
    main()