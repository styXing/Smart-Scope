import RPi.GPIO as GPIO
import time

# Pin definitions
RED_PIN = 12
GREEN_PIN = 13
TRIGGER_PIN = 5
ECHO_PIN = 4

# Constants for distance calculations
SOUND_VELOCITY = 0.034
CM_TO_INCH = 0.393701

def setup():
    # Set GPIO mode to BCM (using Broadcom SOC channel numbers)
    GPIO.setmode(GPIO.BCM)
    # Set up the pins
    GPIO.setup(RED_PIN, GPIO.OUT)
    GPIO.setup(GREEN_PIN, GPIO.OUT)
    GPIO.setup(TRIGGER_PIN, GPIO.OUT)
    GPIO.setup(ECHO_PIN, GPIO.IN)
    # Initial state for trigger pin
    GPIO.output(TRIGGER_PIN, GPIO.LOW)

def get_distance():
    # Reset trigger pin
    GPIO.output(TRIGGER_PIN, GPIO.LOW)
    time.sleep(0.000002)  # 2 microseconds delay
    
    # Set trigger pin high for 10 microseconds
    GPIO.output(TRIGGER_PIN, GPIO.HIGH)
    time.sleep(0.00001)  # 10 microseconds delay
    GPIO.output(TRIGGER_PIN, GPIO.LOW)
    
    # Measure the time the echo pin is HIGH
    start_time = time.time()
    stop_time = time.time()
    
    # Wait for echo pin to go HIGH
    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()
        
    # Wait for echo pin to go LOW
    while GPIO.input(ECHO_PIN) == 1:
        stop_time = time.time()
    
    # Calculate duration in seconds
    duration = stop_time - start_time
    
    # Convert to milliseconds (as in Arduino code)
    duration_ms = duration * 1000
    
    # Calculate distance
    distance_cm = duration_ms * SOUND_VELOCITY / 2
    distance_inch = distance_cm * CM_TO_INCH
    
    return distance_cm, distance_inch

def main():
    try:
        setup()
        print("Ultrasonic distance measurement started")
        
        while True:
            # Get distance measurements
            distance_cm, distance_inch = get_distance()
            
            # Print the distances
            print(f"Distance (cm): {distance_cm:.2f}")
            print(f"Distance (inch): {distance_inch:.2f}")
            print()
            
            # Control LEDs based on distance
            if distance_inch <= 10:
                GPIO.output(GREEN_PIN, GPIO.LOW)
                GPIO.output(RED_PIN, GPIO.HIGH)
            else:
                GPIO.output(RED_PIN, GPIO.LOW)
                GPIO.output(GREEN_PIN, GPIO.HIGH)
            
            # Loop 10 times per second (100ms delay)
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("Measurement stopped by user")
    finally:
        # Clean up GPIO on exit
        GPIO.cleanup()

if __name__ == "__main__":
    main()