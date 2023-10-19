#2023 - 10 - 10
#Samuel Bowles

#this version, I want to start by projecting 3D wireframes onto a 2D screen
#I also want to add support for loading wireframes from files

import math
import tkinter as tk
from tkinter import *

#how to use methods of the Canvas class:
#line = myScreen.create_line(0,0,200,200,fill='white')
#line = myScreen.create_line(0,200,200,0,fill='white')
#myScreen.delete("all") #deletes everything that has been drawn to the canvas

#I'm creating my own class for the screen because it's simpler for me to work with than using the canvas class
class Screen(tk.Canvas):
    #tk.Canvas does not keep track of it's own height and width so we have to do it here
    height = 0
    width = 0
    camera = 0
    shapeDrawList = []
    unitSize = 0
    scrollRate = 0

    def __init__(self, cam, master, width, height, bg, uSize = 10, scroll = 10):
        super(Screen, self).__init__(master = master, width = width, height = height, bg = bg)
        self.height = height
        self.width = width
        self.camera = cam
        self.camera.screen = self
        self.unitSize = uSize
        self.scrollRate = scroll
        self.pack()
        self.updateScreen()

    #methods for converting between grid coordinates and screen coordinates
    def xyToCanvas(self, x, y):
        canvasX = (self.height - (x * self.unitSize + self.height / 2))
        canvasY = (y * self.unitSize + (self.width / 2))
        return [canvasX, canvasY]

    def canvasToXY(self, canvasX, canvasY):
        x = ((self.height / 2) - (self.height - canvasX)) / self.unitSize
        y = ((self.width / 2) - canvasY) / self.unitSize
        return [x, y]
    
    #methods for drawing to the screen
    def drawLine(self, startXY, endXY, colour = "white"):
        screenStart = self.xyToCanvas(startXY[0], startXY[1])
        screenEnd = self.xyToCanvas(endXY[0], endXY[1])
        self.create_line(screenStart[0], screenStart[1], screenEnd[0], screenEnd[1], fill = colour)

    def drawShape(self, shape):
        for edge in shape.edges:
            start3D = edge.startPoint.coords
            end3D = edge.endPoint.coords
            
            lineStart = self.camera.project3DPoint(start3D[0], start3D[1], start3D[2])
            lineEnd = self.camera.project3DPoint(end3D[0], end3D[1], end3D[2])

            #find the distance from the camera to the average of the points in the edge
            relativeX = (start3D[0] + end3D[0] - (2 * self.camera.coords[0])) / 2
            relativeY = (start3D[1] + end3D[1] - (2 * self.camera.coords[1])) / 2
            relativeZ = (start3D[2] + end3D[2] - (2 * self.camera.coords[2])) / 2

            edgeDist = math.sqrt((relativeX ** 2) + (relativeY ** 2) + (relativeZ ** 2))

            #weight the line depending on how far the edge is from the camera on average
            lineWeight = 255 * (1 - (edgeDist / (self.camera.mistMultiplier * self.camera.distance)))
            if lineWeight < 0:
                lineWeight = 0
            elif lineWeight > 255:
                lineWeight = 255
            weightString = (hex(math.floor(lineWeight)))[2:4]
            if len(weightString) < 2:
                weightString = "0" + weightString

            #lineColour = "#00ff00"
            
            #add green proportional to the line weight
            lineColour = "#00" + weightString + "00"
            
            self.drawLine(lineStart, lineEnd, lineColour)
        
    def updateScreen(self):
        self.delete("all")
        
        for shape in self.shapeDrawList:
            self.drawShape(shape)


class Point():
    coords = [0,0,0] #x, y, and z coordinates for 3D points

    def __init__(self, x, y, z):
        self.coords = [x, y, z]
        

class Edge():
    startPoint = 0
    endPoint = 0

    def __init__(self, start, end):
        self.startPoint = start
        self.endPoint = end


class Shape(Point):
    points = []
    edges = []

    def __init__(self, x, y, z, points = [], edges = []):
        super(Shape, self).__init__(x, y, z)
        self.points = self.generatePoints(points)
        self.edges = self.generateEdges(edges)

    def generatePoints(self, xyzList):
        tempPoints = []
        for thisPoint in xyzList:
            tempPoints.append(Point(thisPoint[0], thisPoint[1], thisPoint[2]))
        return tempPoints

    def generateEdges(self, edgeList):
        tempEdges = []
        for thisEdge in edgeList:
            tempEdges.append(Edge(self.points[thisEdge[0]], self.points[thisEdge[1]]))
        return tempEdges


class Camera(Point):
    fLength = 0 #focal length of the simulated camera
    rotation = [0,0,0] #the camera's rotation in the yz, xz, and xy planes (I think I will only be using rotation about the x and y axes)
    drawList = []
    screen = 0
    lastMousePos = [0,0]    #stores the last known position of the mouse cursor for rotating the camera
    distance = 0
    mistMultiplier = 0

    def __init__(self, f = 10, d = 100, r = rotation, m = 1.5):
        super(Camera, self).__init__(0, 0, -d)
        self.fLength = f
        self.rotation = r
        self.distance = d
        self.mistMultiplier = m
    
    def project3DPoint(self, x, y, z):
        camXYZ = self.coords
        camRotXYZ = self.rotation
        pointXYZ = [x, y, z]

        #precompute cosine and sine values of the camera's x y and z axis rotation
        c = [math.cos(camRotXYZ[0]), math.cos(camRotXYZ[1]), math.cos(camRotXYZ[2])]
        s = [math.sin(camRotXYZ[0]), math.sin(camRotXYZ[1]), math.sin(camRotXYZ[2])]

        #precompute the camera's position subtracted from the point's position
        rXYZ = [pointXYZ[0] - camXYZ[0], pointXYZ[1] - camXYZ[1], pointXYZ[2] - camXYZ[2]]
        
        #find the point's position relative to the camera
        dX = c[1] * (s[2] * rXYZ[1] + c[2] * rXYZ[0]) - s[1] * rXYZ[2]
        dY = s[0] * (c[1] * rXYZ[2] + s[1] * (s[2] * rXYZ[1] + c[2] * rXYZ[0])) + c[0] * (c[2] * rXYZ[1] - s[2] * rXYZ[0])
        dZ = c[0] * (c[1] * rXYZ[2] + s[1] * (s[2] * rXYZ[1] + c[2] * rXYZ[0])) - s[0] * (c[2] * rXYZ[1] - s[2] * rXYZ[0]) - self.fLength

        #find the projected x and y screen coordinates
        pX = (self.fLength * dX) / (self.fLength + dZ)
        pY = (self.fLength * dY) / (self.fLength + dZ)

        return [pX, pY]

    #rotating the camera around the origin
    def moveMouse(self, event):
        mousePos = self.screen.canvasToXY(event.x, event.y)
        
        positionDelta = [(mousePos[0] - self.lastMousePos[0]) * self.screen.scrollRate,
                         (mousePos[1] - self.lastMousePos[1]) * self.screen.scrollRate
                         ]
        
        self.lastMousePos = mousePos

        #adjust camera's rotation and position to rotate around the origin (only about the x and y axes (no rotation in the camera's xy plane)
        rotationDelta = [(positionDelta[1] / self.screen.width) * 2 * math.pi, -(positionDelta[0] / self.screen.height) * 2 * math.pi]
        self.rotation[0] += rotationDelta[0]
        self.rotation[1] += rotationDelta[1]

        #clamp the camera's rotation in the yz plane between +- (pi / 2) radians
        if self.rotation[0] > math.pi / 2:
            self.rotation[0] = math.pi / 2
        elif self.rotation[0] < -math.pi / 2:
            self.rotation[0] = -math.pi / 2

        #adjust camera's coordinates so that it is facing the origin [0,0,0]
        self.coords[0] = -self.distance * math.sin(self.rotation[1]) * math.cos(self.rotation[0])
        self.coords[1] = self.distance * math.sin(self.rotation[0])
        self.coords[2] = -self.distance * math.cos(self.rotation[0]) * math.cos(self.rotation[1])
        
        self.screen.updateScreen()

    #set the lastMousePos variable because otherwise the camera will jump around annoyingly
    def mouseDown(self, event):
        self.lastMousePos = self.screen.canvasToXY(event.x, event.y)


def getIntData(inputList):
    readData = inputList.split("]")
    dataList = []

    for index in range(len(readData)):
        if len(readData[index]) < 3:
            del readData[index]
        else:
            if readData[index][0] == ",":
                readData[index] = readData[index][1:]
            if readData[index][0] == "[":
                readData[index] = readData[index][1:]
            data = readData[index].split(",")

            for i in range(len(data)):
                if "." in data[i]:
                    data[i] = float(data[i])
                else:
                    data[i] = int(data[i])
            dataList.append(data)
            
    return dataList

def getShape(fileName):
    shapeFile = open(fileName, "r").read().split("\n")
    
    readPoints = shapeFile[0]
    pointList = getIntData(readPoints)

    readEdges = shapeFile[1]
    edgeList = getIntData(readEdges)
            
    return [pointList, edgeList]

#constants
PHI = (math.sqrt(5) + 1) / 2

#startup variables
screenWidth = 800
screenHeight = 800

#still learning how to use tkinter
root = tk.Tk()
root.title("3D wireframe renderer")
myCamera = Camera(100, 10, m = 1.5)
myScreen = Screen(cam = myCamera, master = root, width = screenWidth, height = screenHeight, bg = "black")

#slightly less repeated code than before:
cubePointsEdges = getShape("cube.txt")
icoPointsEdges = getShape("icosahedron.txt")
dodecaPointsEdges = getShape("dodecahedron.txt")
octaPointsEdges = getShape("octahedron.txt")
tetraPointsEdges = getShape("tetrahedron.txt")

#myCube = Shape(0,0,0, points = cubePointsEdges[0], edges = cubePointsEdges[1])
#myIco = Shape(0,0,0, points = icoPointsEdges[0], edges = icoPointsEdges[1])
myDodeca = Shape(0,0,0, points = dodecaPointsEdges[0], edges = dodecaPointsEdges[1])
#myOcta = Shape(0,0,0, points = octaPointsEdges[0], edges = octaPointsEdges[1])
#myTetra = Shape(0,0,0, points = tetraPointsEdges[0], edges = tetraPointsEdges[1])

#myScreen.shapeDrawList.append(myCube)
#myScreen.shapeDrawList.append(myIco)
myScreen.shapeDrawList.append(myDodeca)
#myScreen.shapeDrawList.append(myOcta)
#myScreen.shapeDrawList.append(myTetra)

root.bind("<B1-Motion>", myCamera.moveMouse)
root.bind("<Button-1>", myCamera.mouseDown)

myScreen.updateScreen()
myScreen.mainloop()
