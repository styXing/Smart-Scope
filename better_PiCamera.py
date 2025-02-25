#!/usr/bin/env python3

import cv2
import numpy as np
import time
from picamera2 import Picamera2
from libcamera import Transform
import threading

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
        """Initialize and start the Picamera2"""
        self.running = True
        
        # Initialize the camera
        self.picam2 = Picamera2()
        
        # Configure the camera
        config = self.picam2.create_video_configuration(
            main={"size": (self.width, self.height), "format": "BGR888"},
            controls={"FrameDurationLimits": (int(1/self.fps * 1000000), int(1/self.fps * 1000000))},
            transform=Transform(vflip=False, hflip=False)
        )
        self.picam2.configure(config)
        
        # Start the camera
        self.picam2.start()
        
        # Small delay to allow camera to initialize
        time.sleep(0.5)
        
        # Start the frame capture thread
        self.thread = threading.Thread(target=self._capture_frames)
        self.thread.daemon = True
        self.thread.start()
        
    def _capture_frames(self):
        """Continuously capture frames from the camera"""
        while self.running:
            # Capture a frame
            frame = self.picam2.capture_array()
            
            # Convert from RGB to BGR for OpenCV processing
            if frame.shape[2] == 3:  # Make sure it's a color frame
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            with self.lock:
                self.frame = frame.copy()
            
            # Limit frame rate to avoid high CPU usage
            time.sleep(1.0 / self.fps)
    
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
        
        # Draw mil dots or rangefinder markings
        mil_spacing = 10
        for i in range(1, 5):
            # Horizontal mil dots below crosshair
            cv2.line(output,
                    (self.crosshair_x, self.crosshair_y + i * mil_spacing),
                    (self.crosshair_x, self.crosshair_y + i * mil_spacing),
                    self.crosshair_color, thickness - 1)
                    
            # Vertical mil dots to the right of crosshair
            cv2.line(output,
                    (self.crosshair_x + i * mil_spacing, self.crosshair_y),
                    (self.crosshair_x + i * mil_spacing, self.crosshair_y),
                    self.crosshair_color, thickness - 1)
        
        # Draw sensor data
        y_pos = 30
        for key, value in self.sensor_data.items():
            cv2.putText(output, 
                       f"{key}: {value}", 
                       (10, y_pos), 
                       cv2.FONT_HERSHEY_COMPLEX, 
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
        if hasattr(self, 'picam2'):
            self.picam2.stop()
        cv2.destroyAllWindows()
        
    def save_frame(self, path="scope_capture.jpg"):
        """Save the current frame with overlays to a file"""
        frame = self.get_frame_with_overlay()
        if frame is not None:
            cv2.imwrite(path, frame)
            return True
        return False

# Example usage
if __name__ == "__main__":
    # Create the scope overlay instance
    scope = ScopeOverlay(width=800, height=600, fps=30)
    
    # Start the camera
    scope.start_camera()
    
    # Update with mock sensor data (would come from real sensors)
    scope.update_sensor_data({
        'Wind': '420 mph',
        'Temp': '69°F',
        'Range': '300m',
        'Angle': '2.5°'
    })
    
    # Main loop to simulate changing conditions
    try:
        print("Press 'q' to quit, 's' to save a screenshot")
        while True:
            # Simulate crosshair adjustments based on external factors
            # In reality, this would use your ballistic calculations
            wind_offset = int(np.sin(time.time()) * 50)
            elevation_offset = int(np.cos(time.time() * 0.5) * 25)
            
            # Update the crosshair position
            scope.update_crosshair(x_offset=wind_offset, y_offset=elevation_offset)
            
            # Display the preview
            frame = scope.get_frame_with_overlay()
            if frame is not None:
                cv2.imshow("Scope View", frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Save current frame
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                scope.save_frame(f"scope_capture_{timestamp}.jpg")
                print(f"Screenshot saved as scope_capture_{timestamp}.jpg")
                
            time.sleep(0.033)  # ~30 FPS
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        scope.stop()
        print("Camera stopped")