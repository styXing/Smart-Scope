from picamera import PiCamera
from picamera.array import PiRGBArray
import numpy as np
import cv2
import time

# Initialize camera
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 30
rawCapture = PiRGBArray(camera, size=(640, 480))

# Allow camera to warm up
time.sleep(0.1)

# Create an overlay for drawing
overlay = None
overlay_width, overlay_height = 640, 480

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    image = frame.array
    
    # Create a transparent overlay
    overlay_img = np.zeros((overlay_height, overlay_width, 4), dtype=np.uint8)
    
    # In the future, these coordinates would be calculated
    crosshair_x, crosshair_y = 320, 240
    
    # Draw crosshair on overlay
    cv2.line(overlay_img, 
             (crosshair_x - 20, crosshair_y), 
             (crosshair_x + 20, crosshair_y), 
             (0, 255, 0, 255), 2)
    cv2.line(overlay_img, 
             (crosshair_x, crosshair_y - 20), 
             (crosshair_x, crosshair_y + 20), 
             (0, 255, 0, 255), 2)
    
    # Add text for sensor data
    cv2.putText(overlay_img, 
                "Wind: 5.2 mph", 
                (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, (255, 255, 255, 255), 2)
    
    # Remove previous overlay if it exists
    if overlay:
        camera.remove_overlay(overlay)
    
    # Add new overlay
    overlay = camera.add_overlay(overlay_img.tobytes(), 
                                 size=(overlay_width, overlay_height),
                                 layer=3,
                                 alpha=255,
                                 fullscreen=False,
                                 window=(0, 0, overlay_width, overlay_height))
    
    # Clear the stream for the next frame
    rawCapture.truncate(0)
    
    # Press 'q' to exit
    if cv2.waitKey(1) == ord('q'):
        break

camera.close()