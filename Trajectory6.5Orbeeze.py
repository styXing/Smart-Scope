import math
import time
#import cv2
#from picamera2 import Picamera2



def calculateVertDropCreedmoor(distance):
    """his function calculates the vertical drop in Imperial Units based on the distance to the target.

    Param: distance: float - the distance in meters to the target.
    
    Return: VertDrop: float - the distance in centimeters of the vertical drop of the bullet by the desired meters
    
    The numbers below were found via quadratic regression on excel. The R^2 value for this equation is 0.9991.
    """
    distanceFeet = distance / 0.3048
    return (((-0.0004 * (distanceFeet ** 2)) + (0.0861 * distanceFeet) - 2.0143) * 2.54)
    

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
        return (((-0.0368 * (distanceFeet ** 2)) + (2.2546 * distanceFeet) -32.054) * 2.54)

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

    sceneHeightCM = ((2 * math.tan(math.radians(vertFOVinDeg / 2)) * distance) * 100)

    vertDropCM = calculateVertDropOrbeeze(distance) #Change this method to change caliber

    #print(vertDropCM)
    pixelsPerCentimeter = imageHeight / sceneHeightCM
    pixelsOfVertDrop = vertDropCM * pixelsPerCentimeter
    
    vertDropPixels = imageHeight // 2 - pixelsOfVertDrop

    return vertDropPixels

def displayVertTranslation(targetDistanceMeters):
    crosshairX = 320
    crosshairY = 240

    picam = Picamera2()
    picam.start()
    time.sleep(2)
    while True:
        img.picam.capture_array()
        img = cv2.drawMarker(img, (crosshairX, crosshairY), (0, 0, 0), cv2.MARKER_CROSS, 90, 1)
        img = cv2.circle(img, (crosshairX, calculateVertTranslation(targetDistanceMeters)), 3, (0,0, 255), 4)
        cv2.imshow("Output", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    picam.stop()
    picam.close()


def main():
    while True:
        targetDistanceFeet = float(input())
        targetDistanceMeters= targetDistanceFeet * 0.3048
        #print(calculateVertTranslation(targetDistanceMeters))
        displayVertTranslation(targetDistanceMeters)

if __name__ == "__main__":
    main()


#def verticalDropDisplay(distance):
