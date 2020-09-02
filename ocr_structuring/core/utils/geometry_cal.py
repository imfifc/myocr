import math


def rotate_vector(coor, angle, relative_coor=(0, 0)):
    rad_theta = math.radians(angle)
    cos_theta = math.cos(rad_theta)
    sin_theta = math.sin(rad_theta)
    x = (coor[0] - relative_coor[0]) * cos_theta - \
        (coor[1] - relative_coor[1]) * sin_theta + relative_coor[0]
    y = (coor[1] - relative_coor[1]) * cos_theta + \
        (coor[0] - relative_coor[0]) * sin_theta + relative_coor[1]
    return [x, y]
