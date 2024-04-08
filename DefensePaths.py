import math, random
from panda3d.core import *
from panda3d.core import Vec3

def Cloud(radius = 1):
    x = 2 * random.random() - 1
    y = 2 * random.random() - 1
    z = 2 * random.random() - 1
    unitVec = Vec3(x, y, z)
    unitVec.normalize()
    return unitVec * radius

def BaseballSeams(step, numSeams, B, F = 1):
    time = step / float (numSeams) * 2 * math.pi

    F4 = 0

    R = 1

    xxx = math.cos(time) - B * math.cos(3 * time)
    yyy = math.sin(time) + B * math.sin(3 * time)
    zzz = F * math.cos(2 * time) + F4 * math.cos(4 * time)

    rrr = math.sqrt(xxx ** 2 + yyy ** 2 + zzz ** 2)

    x = R * xxx / rrr
    y = R * yyy / rrr
    z = R * zzz / rrr

    return Vec3(x, y, z)

def CircleXY(radius=1, numPoints=30):
    points = []
    for i in range(numPoints):
        theta = i / numPoints * 2 * math.pi
        x = radius * math.cos(theta)
        y = radius * math.sin(theta)
        points.append(Vec3(x, y, 0))
    return points

def CircleXZ(radius = 1, numPoints = 30):
    points = []
    for i in range(numPoints):
        theta = i / numPoints * 2 * math.pi
        x = radius * math.cos(theta)
        z = radius * math.sin(theta)
        points.append(Vec3(x, 0, z))
    return points
     
def CircleYZ(radius = 1, numPoints = 30):
    points = []
    for i in range(numPoints):
        theta = i / numPoints * 2 * math.pi
        y = radius * math.cos(theta)
        z = radius * math.sin(theta)
        points.append(Vec3(0, y, z))
    return points