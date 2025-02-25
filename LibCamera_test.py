#!/usr/bin/env python3

import cv2
import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont
import threading
import subprocess as sp
import os

class ScopeOverlay:
    def __init__(self, width=640, height=480, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self.crosshair_x = width // 2
        self.crosshair_y = height // 2
        self.crosshair_color = (0, 255, 0)  # Green by default
        self.sensor_data = {}
        self.running = False
        self.frame = None
        self.lock = threading.Lock()
        
    def start_camera(self):
        """Start the libcamera process and read frames"""
        self.running = True
        
        # Create a pipe for libcamera to write to
        cmd = [
            'libcamera-vid',
            '-t', '0',           # Run indefinitely
            '--width', str(self.width),
            '--height', str(self.height),
            '--framerate', str(self.fps),
            '--codec', 'yuv420',  # Use raw format
            '-o', '-'            # Output to stdout
        ]
        
        # Start the process
        self.process = sp.Popen(cmd, stdout=sp.PIPE)
        
        # Calculate the frame size
        frame_size = self.width * self.height * 3 // 2  # For YUV420
        
        # Read frames in a separate thread
        self.thread = threading.Thread(target=self._read_frames, args=(frame_size,))
        self.thread.daemon = True
        self.thread.start()
        
    def _read_frames(self, frame_size):
        """Read frames from the libcamera process"""
        while self.running:
            # Read a full frame
            raw_frame = self.process.stdout.read(frame_size)
            if not raw_frame or len(raw_frame) != frame_size:
                break
                
            # Convert YUV420 to BGR
            yuv = np.frombuffer(raw_frame, dtype=np.uint8).reshape((self.height * 3 // 2, self.width))
            bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
            
            with self.lock:
                self.frame = bgr.copy()
    
    def update_crosshair(self, x_offset=0, y_offset=0, color=None):
        """Update the crosshair position based on ballistic calculations"""
        self.crosshair_x = self.width // 2 + x_offset
        self.crosshair_y = self.height // 2 + y_offset
        
        if color:
            self.crosshair_color = color
    
    def update_sensor_data(self, data):
        """Update the sensor data to be displayed"""
        self.sensor_data = data
    
    def get_frame_with_overlay(self):
        """Get the current frame with overlays applied"""
        with self.lock:
            if self.frame is None:
                return None
            
            # Make a copy to avoid modifying the original
            output = self.frame.copy()
        
        # Draw crosshair
        size = 20
        thickness = 2
        
        # Horizontal line
        cv2.line(output, 
                (self.crosshair_x - size, self.crosshair_y), 
                (self.crosshair_x + size, self.crosshair_y), 
                self.crosshair_color, thickness)
        
        # Vertical line
        cv2.line(output, 
                (self.crosshair_x, self.crosshair_y - size), 
                (self.crosshair_x, self.crosshair_y + size), 
                self.crosshair_color, thickness)
        
        # Optional: Add mil dots or rangefinder markings
        mil_spacing = 10
        for i in range(1, 5):
            # Horizontal mil dots below crosshair
            cv2.line(output,
                    (self.crosshair_x, self.crosshair_y + i * mil_spacing),
                    (self.crosshair_x, self.crosshair_y + i * mil_spacing),
                    self.crosshair_color, thickness)
        
        # Draw sensor data
        y_pos = 30
        for key, value in self.sensor_data.items():
            cv2.putText(output, 
                      f"{key}: {value}", 
                      (10, y_pos), 
                      cv2.FONT_HERSHEY_SIMPLEX, 
                      0.6, (255, 255, 255), 2)
            y_pos += 25
        
        return output
    
    def display_preview(self):
        """Show a preview window with the overlay"""
        cv2.namedWindow("Scope View", cv2.WINDOW_NORMAL)
        
        while self.running:
            frame = self.get_frame_with_overlay()
            if frame is not None:
                cv2.imshow("Scope View", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.stop()
                break
    
    def stop(self):
        """Stop the camera and clean up"""
        self.running = False
        if hasattr(self, 'process'):
            self.process.terminate()
            self.process.wait()
        cv2.destroyAllWindows()

# Example usage
if __name__ == "__main__":
    # Create the scope overlay instance
    scope = ScopeOverlay(width=800, height=600, fps=30)
    
    # Start the camera
    scope.start_camera()
    
    # Update with mock sensor data (would come from real sensors)
    scope.update_sensor_data({
        'Wind': '5.2 mph',
        'Temp': '72°F',
        'Range': '300m',
        'Angle': '2.5°'
    })
    
    # Main loop to simulate changing conditions
    try:
        while True:
            # Simulate crosshair adjustments based on external factors
            # In reality, this would use your ballistic calculations
            wind_offset = int(np.sin(time.time()) * 10)
            
            # Update the crosshair position
            scope.update_crosshair(x_offset=wind_offset, y_offset=0)
            
            # Display the preview
            frame = scope.get_frame_with_overlay()
            if frame is not None:
                cv2.imshow("Scope View", frame)
            
            # Exit on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
            time.sleep(0.05)  # Small delay to prevent high CPU usage
            
    except KeyboardInterrupt:
        pass
    finally:
        scope.stop()