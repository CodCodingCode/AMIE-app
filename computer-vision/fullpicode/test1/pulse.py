import time
import qwiic_max3010x
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# Initialize sensor
sensor = qwiic_max3010x.QwiicMax3010x()

if not sensor.connected:
    print("MAX30105 not connected. Check wiring.")
    exit()

sensor.setup()  # Default configuration: 69 samples/sec, LED power medium
sensor.set_led_pulse_amplitude_red(0x1F)  # Moderate LED brightness
sensor.set_led_pulse_amplitude_green(0)   # Green off (not used for pulse)

print("Starting pulse measurement. Press Ctrl+C to stop.")

ir_values = []
time_stamps = []

try:
    start_time = time.time()
    
    while True:
        if sensor.available():
            ir = sensor.get_ir()  # IR light absorption reflects pulse
            timestamp = time.time() - start_time
            
            ir_values.append(ir)
            time_stamps.append(timestamp)
            
            print(f"IR: {ir}")
            
            # Keep only last 5 seconds of data for real-time plot
            if len(ir_values) > 500:
                ir_values = ir_values[-500:]
                time_stamps = time_stamps[-500:]
            
            time.sleep(0.01)  # 100 Hz sampling approx.

except KeyboardInterrupt:
    print("Stopped. Processing data...")

    # Basic peak detection for heart rate (offline example)
    ir_array = np.array(ir_values)
    time_array = np.array(time_stamps)
    
    # Normalize
    ir_array = ir_array - np.mean(ir_array)
    
    # Find peaks
    peaks, _ = find_peaks(ir_array, distance=30)  # Adjust 'distance' for real data
    
    # Calculate heart rate
    peak_times = time_array[peaks]
    intervals = np.diff(peak_times)
    
    if len(intervals) > 0:
        avg_interval = np.mean(intervals)
        bpm = 60 / avg_interval
        print(f"Estimated Heart Rate: {bpm:.1f} BPM")
    else:
        print("No peaks detected.")
    
    # Plot IR signal and peaks
    plt.plot(time_array, ir_array, label='IR Signal')
    plt.plot(peak_times, ir_array[peaks], 'rx', label='Peaks')
    plt.xlabel('Time (s)')
    plt.ylabel('IR Value')
    plt.title('Pulse Signal')
    plt.legend()
    plt.show()
