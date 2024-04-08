from direct.task import Task
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from CollideObjectBase import *
from panda3d.core import CollisionHandlerEvent
from direct.interval.LerpInterval import LerpFunc
from direct.particles.ParticleEffect import ParticleEffect
from panda3d.core import Filename
from direct.task.Task import TaskManager
import DefensePaths as defensePaths
#Regex module import for string editing
import re
from panda3d.core import NodePath
from direct.interval.IntervalGlobal import Sequence
import math, random


class Universe(InverseSphereCollideObject):
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float):
        super(Universe, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), .9)
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)

        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)

class Planet(SphereCollideObject):
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float):
        super(Planet, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 1.1)
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)

        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)

class SpaceStation(CapsuleCollidableObject):
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str, posVec: Vec3, Hpr: Vec3 , scaleVec: float):
        super(SpaceStation, self).__init__(loader, modelPath, parentNode, nodeName, 2, -1, 5, 1, -1, -5, 20)
        self.modelNode.setPos(posVec)
        self.modelNode.setHpr(Hpr)
        self.modelNode.setScale(scaleVec)
        
class Player(SphereCollideObject):
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float, taskMgr, render, accept, traverser, DroneHitScore):
        super(Player, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 10) #Changes radius value of drone
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)

        self.taskMgr = taskMgr
        self.render = render
        self.accept = accept

        self.reloadTime = .25
        self.missileDistance = 1000
        self.missileBay = 1

        self.droneHitScore = DroneHitScore

        self.boostActive = False
        self.boostCooldownActive = False
        self.rate = 5


        self.SetParticles()

        self.SetKeyBindings()

        #Checks Intervals Dictionary
        self.taskMgr.add(self.CheckIntervals, "checkMissiles", 34)

        self.cntExplode = 0
        self.explodeIntervals = {}

        self.traverser = traverser
        self.handler = CollisionHandlerEvent()

        self.handler.addInPattern('into')
        self.accept('into', self.HandleInto)

    def HandleInto(self, entry):
        fromNode = entry.getFromNodePath().getName()
        print("fromNode: " + fromNode)
        intoNode = entry.getIntoNodePath().getName()
        print("intoNode: " + intoNode)
        intoPosition = Vec3(entry.getSurfacePoint(self.render))

        tempVar = fromNode.split('_')
        shooter = tempVar[0]
        tempVar = intoNode.split('-')
        tempVar = intoNode.split('_')
        victim = tempVar[0]
        
        pattern = r'[0-9]'
        strippedString = re.sub(pattern, '', victim)
        print(strippedString)

        if (strippedString == "Drone"):
            Missile.Intervals[shooter].finish()
            self.DroneDestroy(victim, intoPosition)
        if (strippedString == "drone"):
            Missile.Intervals[shooter].finish()
            self.DroneDestroy(victim, intoPosition)
        elif (strippedString == "Planet"):
            Missile.Intervals[shooter].finish()
            self.PlanetDestroy(victim)
        elif (strippedString == "Space Station"):
            Missile.Intervals[shooter].finish()
            self.SpaceStationDestroy(victim)
        else:
            Missile.Intervals[shooter].finish()

    def DroneDestroy(self, hitID, hitPosition):
        nodeID = self.render.find(hitID)
        nodeID.detachNode()

        self.droneHitScore()

        self.explodeNode.setPos(hitPosition)
        self.Explode(hitPosition)


    def Explode(self, impactPoint):
        self.cntExplode += 1
        tag = 'particles-' + str(self.cntExplode)

        self.explodeIntervals[tag] = LerpFunc(self.ExplodeLight, fromData = 0, toData = 1, duration = 4.0, extraArgs = [impactPoint])
        self.explodeIntervals[tag].start()

    def ExplodeLight(self, t, explosionPosition):
        if t == 1.0 and self.explodeEffect:
            self.explodeEffect.disable()
        elif t == 0:
            self.explodeEffect.start(self.explodeNode)

    def SetParticles(self):
        base.enableParticles()
        self.explodeEffect = ParticleEffect()
        self.explodeEffect.loadConfig("./Assets/ParticleEffects/Explosions/basic_xpld_efx.ptf")
        self.explodeEffect.setScale(20)
        self.explodeNode = self.render.attachNewNode('ExplosionEffects')
        self.droneHitScore()
    
    def Fire(self):
        if self.missileBay:
            travRate = self.missileDistance
            aim = self.render.getRelativeVector(self.modelNode, Vec3.forward()) #The direction the ship is facing
            aim.normalize()

            fireSolution = aim * travRate
            inFront = aim * 150
            travVec = fireSolution + self.modelNode.getPos()
            self.missileBay -= 1
            tag = "Missle" + str(Missile.missileCount)
            posVec = self.modelNode.getPos() + inFront #Spawns missile in front of the nose of the ship
            currentMissile = Missile(loader, "./Assets/Phaser/phaser.egg", self.render, tag, posVec, 4.0) #Create our missile
            Missile.Intervals[tag] = currentMissile.modelNode.posInterval(2.0, travVec, startPos = posVec, fluid = 1)
            Missile.Intervals[tag].start()
            self.traverser.addCollider(currentMissile.collisionNode, self.handler)
        else:
            #When we're not reloading, start reloading
            if not self.taskMgr.hasTaskNamed("reload"):
                print("Initializing reload...")
                self.taskMgr.doMethodLater(0, self.Reload, "reload")
                return Task.cont
            
    def Reload(self, task):
        if task.time > self.reloadTime:
            self.missileBay += 1
            print ("Reload Complete.")
            return Task.done
        if self.missileBay > 1:
            self.missileBay = 1
        elif task.time <= self.reloadTime:
            print("Reload proceeding...")
            return Task.cont
    
    def CheckIntervals(self, task):
        keys_to_delete = []
        for i in Missile.Intervals:
            if not Missile.Intervals[i].isPlaying():
                Missile.cNodes[i].detachNode()
                Missile.fireModels[i].detachNode()
                if i in Missile.collisionSolids:  # Check if the key exists
                    del Missile.collisionSolids[i]
                keys_to_delete.append(i)

        for key in keys_to_delete:
            del Missile.Intervals[key]
            del Missile.fireModels[key]
            del Missile.cNodes[key]

        return Task.cont
        
    def SetKeyBindings(self):
        self.accept("space", self.Thrust, [1])
        self.accept("space-up", self.Thrust, [0])
        self.accept("a", self.LeftTurn, [1])
        self.accept("a-up", self.LeftTurn, [0])
        self.accept("d", self.RightTurn, [1])
        self.accept("d-up", self.RightTurn, [0])
        self.accept("w", self.UpTurn, [1])
        self.accept("w-up", self.UpTurn, [0])
        self.accept("s", self.DownTurn, [1])
        self.accept("s-up", self.DownTurn, [0])
        self.accept("e", self.RightRoll, [1])
        self.accept("e-up", self.RightRoll, [0])
        self.accept("q", self.LeftRoll, [1])
        self.accept("q-up", self.LeftRoll, [0])
        self.accept('f', self.Fire)
        self.accept("shift", self.activateBoost)

    def activateBoost(self):
        if not self.boostActive and not self.boostCooldownActive:
            self.boostActive = True
            self.rate *= 2
            self.taskMgr.doMethodLater(5, self.deactivateBoost, "boost-cooldown")

    def deactivateBoost(self, taskMgr):
        self.boostActive = False
        self.rate /= 2
        self.boostCooldownActive = True
        self.taskMgr.doMethodLater(10, self.resetBoostCooldown, "reset-boost-cooldown") #Cooldown timer
        return Task.done

    def resetBoostCooldown(self, task):
        self.boostCooldownActive = False
        return Task.done

    def Thrust(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyThrust, "forward-thrust")
        else:
            self.taskMgr.remove("forward-thrust")

    def ApplyThrust(self, task):
        trajectory = self.render.getRelativeVector(self.modelNode, Vec3.forward())
        trajectory.normalize()
        self.modelNode.setFluidPos(self.modelNode.getPos() + trajectory * self.rate)
        return Task.cont
    
    def LeftTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyLeftTurn, "left-turn")
        else:
            self.taskMgr.remove("left-turn")

    def ApplyLeftTurn(self, task):
        rate = .5
        self.modelNode.setH(self.modelNode.getH() + rate)
        return Task.cont
    
    def RightTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyRightTurn, "right-turn")
        else:
            self.taskMgr.remove("right-turn")

    def ApplyRightTurn(self, task):
        rate = .5
        self.modelNode.setH(self.modelNode.getH() - rate)
        return Task.cont
    
    def UpTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyUpTurn, "up-turn")
        else:
            self.taskMgr.remove("up-turn")

    def ApplyUpTurn(self, task):
        rate = .5
        self.modelNode.setP(self.modelNode.getP() + rate)
        return Task.cont
    
    def DownTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyDownTurn, "down-turn")
        else:
            self.taskMgr.remove("down-turn")

    def ApplyDownTurn(self, task):
        rate = .5
        self.modelNode.setP(self.modelNode.getP() - rate)
        return Task.cont
    
    def RightRoll(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyRightRoll, "right-roll")
        else:
            self.taskMgr.remove("right-roll")

    def ApplyRightRoll(self, task):
        rate = .5
        self.modelNode.setR(self.modelNode.getR() + rate)
        return Task.cont
    
    def LeftRoll(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyLeftRoll, "left-roll")
        else:
            self.taskMgr.remove("left-roll")

    def ApplyLeftRoll(self, task):
        rate = .5
        self.modelNode.setR(self.modelNode.getR() - rate)
        return Task.cont
    
    def PlanetDestroy(self, victim: NodePath):
        nodeID = self.render.find(victim)

        self.taskMgr.add(self.PlanetShrink, name = "PlanetShrink", extraArgs = [nodeID], appendTask = True)

    def PlanetShrink(self, nodeID: NodePath, task):
        if task.time < 2.0:
            if nodeID.getBounds().getRadius() > 0:
                scaleSubtraction = 10
                nodeID.setScale(nodeID.getScale() - scaleSubtraction)
                temp = 30 * random.random()
                nodeID.setH(nodeID.getH() + temp)
                return task.cont
        else:
            nodeID.detachNode()
            return task.done
        
    def SpaceStationDestroy(self, victim: NodePath):
        nodeID = self.render.find(victim)

        self.taskMgr.add(self.SpaceStationShrink, name = "SpaceStationShrink", extraArgs = [nodeID], appendTask = True)

    def SpaceStationShrink(self, nodeID: NodePath, task):
        if task.time < 2.0:
            if nodeID.getBounds().getRadius() > 0:
                scaleSubtraction = 2
                nodeID.setScale(nodeID.getScale() - scaleSubtraction)
                temp = 30 * random.random()
                nodeID.setH(nodeID.getH() + temp)
                return task.cont
        else:
            nodeID.detachNode()
            return task.done

class Drone(SphereCollideObject):
    droneCount = 0
    
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float):
        super(Drone, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 3)
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)

        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)

class Missile(SphereCollideObject):
    fireModels = {}
    cNodes = {}
    collisionSolids = {}
    Intervals = {}
    missileCount = 0

    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float = 1.0):
        super(Missile, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 3.0)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setPos(posVec)

        Missile.missileCount += 1
        Missile.fireModels[nodeName] = self.modelNode
        Missile.cNodes[nodeName] = self.collisionNode

class Orbiter(SphereCollideObject):
    numOrbits = 0
    velocity = 0.005
    cloudTimer = 240

    def __init__(self, loader: Loader, taskMgr: TaskManager, modelPath: str, parentNode: NodePath, nodeName: str, scaleVec: Vec3, texPath: str, centralObject: PlacedObject, orbitRadius: float, orbitType: str, staringAt: Vec3):
        super(Orbiter, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 3.2)\
        
        self.taskMgr = taskMgr
        self.orbitType = orbitType
        self.modelNode.setScale(scaleVec)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.orbitObject = centralObject
        self.orbitRadius = orbitRadius
        self.staringAt = staringAt
        Orbiter.numOrbits += 1

        self.cloudClock = 0
        
        self.taskFlag = "Traveler-" + str(Orbiter.numOrbits)
        taskMgr.add(self.Orbit, self.taskFlag)

    def Orbit(self, task):
        if self.orbitType == "MLB":
            positionVec = defensePaths.BaseballSeams(task.time * Orbiter.velocity, self.numOrbits, 2.0)
            self.modelNode.setPos(positionVec * self.orbitRadius + self.orbitObject.modelNode.getPos())
        elif self.orbitType == "Cloud":
            if self.cloudClock < Orbiter.cloudTimer:
                self.cloudClock += 1
            else:
                self.cloudClock = 0
                positionVec = defensePaths.Cloud()
                self.modelNode.setPos(positionVec * self.orbitRadius + self.orbitObject.modelNode.getPos())
        self.modelNode.lookAt(self.staringAt.modelNode)
        return task.cont
    
class Wanderer(SphereCollideObject):
    numWanderers = 0

    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, modelName: str, scaleVec: Vec3, texPath: str, staringAt: Vec3):
        super(Wanderer, self).__init__(loader, modelPath, parentNode, modelName, Vec3(0, 0,0), 3.2)

        self.modelNode.setScale(scaleVec)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.staringAt = staringAt
        Wanderer.numWanderers += 1

        posInterval0 = self.modelNode.posInterval(20, Vec3(300, 6000, 500), startPos = Vec3(0 , 0, 0))
        posInterval1 = self.modelNode.posInterval(20, Vec3(700, -2000, 100), startPos = Vec3(300 , 6000, 500))
        posInterval2 = self.modelNode.posInterval(20, Vec3(0, -900, -1400), startPos = Vec3(700 , -2000, 100))

        self.travelRoute = Sequence(posInterval0, posInterval1, posInterval2, name = "Traveler")

        self.travelRoute.loop()


