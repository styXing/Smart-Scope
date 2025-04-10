import math


def calculateVertDropCreedmoor(distance):
    """his function calculates the vertical drop in Imperial Units based on the distance to the target.

    Param: distance: int - the distance in _______ to the target
    
    Return: VertDrop: int - the distance in inches of the vertical drop of the bullet by the desired meters
    
    The numbers below were found via quadratic regression on excel. The R^2 value for this equation is 0.9991.
    """
    return ((-0.0004 * (distance ** 2)) + (0.0861 * distance) - 2.0143)
    

def calculateVertDropOrbeeze(distance):
    """This function calculates the vertical drop in Imperial Units based on the distance to the target.

    Param: distance: int - the distance in _______ to the target.
    
    Return: VertDrop: int - the distance in inches of the vertical drop of the bullet by the desired meters.
    
    The numbers below were found via polynomial/quadratic regression to the 3rd and second order, respectiviely.
    The R^2 value for the first equation is 0.9304.
    The R^2 value for the second equation is 0.9691.
    """
    if (distance <= 30.88):
        return ((-0.0006 * (distance ** 3)) + (0.0206 * (distance ** 2)) + (0.0128 * distance) + 0.1082)
    else:
        return ((-0.0368 * (distance ** 2)) + (2.2546 * distance) -32.054)

    #An algorithm based on all the full series of data points rather than two halves.
    # ((-0.0003 * (distance ** 3)) + (0.0109 * (distance ** 2)) + (0.0736 * distance) + 0.1339)
    


while True:
    n = int(input())
    print(calculateVertDropOrbeeze(n))