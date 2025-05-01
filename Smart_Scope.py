import math
import time
import cv2
import serial
import threading
from picamera2 import Picamera2
from datetime import datetime as dt

ser = serial.Serial("/dev/ttyS0", 115200)

global_lidar_distance = 0
global_lidar_strength = 0
global_lidar_temp_celsius = 0
global_cpu_temp_celsius = 0

def checkTemperatureSensors():
    global global_lidar_temp_celsius
    global global_cpu_temp_celsius

    path_to_cpu_temp = open('/sys/class/thermal/thermal_zone0/temp' , 'rt')

    print(f'[info] Starting monitoring temperatures')
    while True:
        time.sleep(1)

        global_cpu_temp_celsius = int(path_to_cpu_temp.read()) / 1000
        path_to_cpu_temp.seek(0)

        if global_cpu_temp_celsius >=70 :
            print(f'[WARNING] CPU Core temperature: {global_cpu_temp_celsius} Celsius')

        if global_lidar_temp_celsius >= 60 :
            print(f'[WARNING] LIDAR sensor temperature: {global_lidar_temp_celsius} Celsius')

def getLidarSensorData():
    global global_lidar_distance
    global global_lidar_strength
    global global_lidar_temp_celsius

    print(f'[info] Receiving data from LIDAR sensor')

    try:
        if ser.is_open == False:
            ser.open()
        while True:
            count = ser.in_waiting
            if count > 8:
                recv = ser.read(9)
                ser.reset_input_buffer()
                if (recv[0] == 0x59 and recv[1] == 0x59) or (recv[0] == 'Y' and recv[1] == 'Y'):
                    distance = recv[2] + recv[3] * 256
                    strength = recv[4] + recv[5] * 256
                    temperature = recv[6] + recv[7] * 256
                    temperature = (temperature/8) - 256
                    checksum = 0

                    if distance == 65535 or strength < 10:
                        print(f'[frame drop:sensor] LIDAR signal strength too low')
                        continue
                    elif distance == 65534 or distance == 65535:
                        print(f'[frame drop:sensor] LIDAR signal too saturated')
                        continue
                    elif distance == 65532:
                        print(f'[frame drop:sensor] Bad LIDAR data or interference')
                        continue

                    for byte in recv[:8]:
                        checksum += byte
                    checksum = checksum & 0xFF

                    if checksum != recv[8]:
                        print(f'[frame drop:sensor] Checksum failed')
                        continue
                    
                    global_lidar_distance = distance
                    global_lidar_strength = strength
                    global_lidar_temp_celsius = temperature

    except OSError:
        print('[WARNING] OSError. Thread was running after Serial was closed.')
    except IOError:
        print(f'[FATAL ERROR] IOError Exception. Serial.read() sufferred an error. Check physical connections and retry.')

    finally:
        print('[info] LIDAR sensor interface terminated.')

def calculateVertDropOrbeeze(distance):
    """This function calculates the vertical drop in Imperial Units based on the distance to the target.

    Param: distance: float - the distance in meters to the target.
    
    Return: VertDrop: float - the distance in centimeters of the vertical drop of the bullet by the desired meters.
    
    The numbers below were found via polynomial/quadratic regression to the 3rd and second order, respectiviely.
    The R^2 value for the first equation is 0.9304.
    The R^2 value for the second equation is 0.9691.
    """
    distanceFeet = distance / 0.3048
    if (distanceFeet <= 30.88):
        return (((-0.0006 * (distanceFeet ** 3)) + (0.0206 * (distanceFeet ** 2)) + (0.0128 * distanceFeet) + 0.1082) * 2.54)
    else:
        return (((-0.0368 * (distanceFeet ** 2)) + (2.2546 * distanceFeet) - 32.054) * 2.54)

    #An algorithm based on the full series of data points rather than two halves.
    # ((-0.0003 * (distance ** 3)) + (0.0109 * (distance ** 2)) + (0.0736 * distance) + 0.1339)

def calculateVertTranslation(distance):
    """ HR: The methodology for this code and the code were given via a chatGPT prompt.

    This function calculates the FOV and scene height to translate the verticle drop off 
    of the projectile to display it on the camera.
    
    Param: distance: float - the distance in meters to the target.

    Return: void - display of the verticle drop to the screen.
    """
    sensorHeight = 6.3 #sensor height(mm) of the HQ camera
    focalLength = 50 #focal length(mm) of the fixed arducam lens
    imageHeight = 480 #image height(px) of the HQ camera display

    vertFOVinRad = 2 * math.atan(sensorHeight / (2 * focalLength))
    vertFOVinDeg = math.degrees(vertFOVinRad)

    scopeZeroDistance = 11.8385265 #Different for each Caliber
    sceneHeightCM = ((2 * math.tan(math.radians(vertFOVinDeg / 2)) * scopeZeroDistance) * 100)    
    print('Sceneheight '+ str(sceneHeightCM))
    try:
        vertDropCM = calculateVertDropOrbeeze(distance) #Change this method to change caliber
    except ZeroDivisionError:
        pass
    print(vertDropCM)
    try:
        pixelsPerCentimeter = imageHeight / sceneHeightCM
    except UnboundLocalError:
        pass
    print(pixelsPerCentimeter)
    pixelsOfVertDrop = vertDropCM * pixelsPerCentimeter
    print(pixelsOfVertDrop)
    vertDropPixels = imageHeight / 2 - pixelsOfVertDrop
    print(vertDropPixels)
    return vertDropPixels

def main():

    global global_lidar_distance
    global global_lidar_strength
    global global_lidar_temp_celsius
    global global_cpu_temp_celsius

    thread_getLidarSensorData = threading.Thread(target = getLidarSensorData, daemon=True)
    thread_checkTemperatureSensors = threading.Thread(target = checkTemperatureSensors, daemon=True)

    try:
        thread_checkTemperatureSensors.start()
        thread_getLidarSensorData.start()

        crosshairX = 320
        crosshairY = 240
        picam = Picamera2()
        picam.configure(picam.create_video_configuration(raw={"size":(1640,1232)},main={"format":'RGB888',"size":(640,480)}))
        picam.start()

        # targetDistanceFeet = float(input())
        while True:

            targetDistanceFeet = global_lidar_distance / 30.48
            targetDistanceMeters = targetDistanceFeet * 0.3048
            # print(calculateVertTranslation(targetDistanceMeters))
            print(f"[debug] Distance in cm:\t"+ str(global_lidar_distance))
            print(f"[debug] Last Signal Strength:\t" + str(global_lidar_strength))
            print(f"[debug] Last LIDAR Temperature:\t" + str(global_lidar_temp_celsius))
            print(f"[debug] Last CPU Temperature:\t" + str(global_cpu_temp_celsius))
            
            img = picam.capture_array()
            img = cv2.drawMarker(img, (crosshairX, crosshairY), (0, 0, 0), cv2.MARKER_CROSS, 120, 2)
            try:
                crosshairYTrans = int(calculateVertTranslation(targetDistanceMeters))
                print(crosshairYTrans)
                img = cv2.circle(img, (crosshairX, crosshairYTrans), 3, (0,0, 255), -1)
                #img = cv2.circle(img, (crosshairX, crosshairY), 3, (0,0, 255), -1)
            except ZeroDivisionError:
                pass
            cv2.imshow("Output", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                if ser != None:
                    ser.close()
                break
        
        picam.stop()
        picam.close()

    except KeyboardInterrupt:
        print(f'\n.\n.\n[WARNING] Exception:KeyboardInterrupt. Program terminating...')

    finally:
        print(f"[info] Last Distance in cm:\t"+ str(global_lidar_distance))
        print(f"[info] Last Signal Strength:\t" + str(global_lidar_strength))
        print(f"[info] Last LIDAR Temperature:\t" + str(global_lidar_temp_celsius))
        print(f"[info] Last CPU Temperature:\t" + str(global_cpu_temp_celsius))
        print(f'.\n[info] Program terminating.')


if __name__ == "__main__":
    main()


#def verticalDropDisplay(distance):
