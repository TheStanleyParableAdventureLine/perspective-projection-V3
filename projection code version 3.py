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
        canvasX = (x * self.unitSize + self.width / 2)
        canvasY = (self.height - (y * self.unitSize + (self.height / 2)))
        return [canvasX, canvasY]

    def canvasToXY(self, canvasX, canvasY):
        x = ((self.width / 2) - canvasX) / self.unitSize
        y = ((self.height / 2) - (self.height - canvasY)) / self.unitSize
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
            lineColour = "#" + "00" + weightString + "00"
            
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
    shapeFile = ""

    def __init__(self, x, y, z, fileName):
        super(Shape, self).__init__(x, y, z)

        rawFile = open(fileName, "r").read()

        #old code I used to remove all spaces from the file
        #charsChecked = 0
        #while charsChecked < len(rawFile):
        #    if rawFile[charsChecked] == " ":
        #        rawFile = rawFile[:charsChecked] + rawFile[charsChecked + 1:]
        #    else:
        #        charsChecked += 1
                
        self.shapeFile = rawFile.split("\n")
        
        
        self.points = self.generatePoints(self.getIntData(self.shapeFile[0]))
        self.edges = self.generateEdges(self.getIntData(self.shapeFile[1]))

    
    #function for reading data from shape files and returning it as a 2D list
    def getIntData(self, inputList):

        #print(inputList)

        #cut out duplicate square brackets
        if inputList[0:2] == "[[":
            inputList = inputList[1:]
        if inputList[len(inputList) - 2:len(inputList)] == "]]":
            inputList = inputList[:len(inputList)]

        #print("\n" + inputList)
        
        readData = inputList.split("]")
        dataList = []

        for index in range(len(readData) - 1):
            if len(readData[index]) < 3:
                del readData[index]
            else:
                if readData[index][0] == ",":
                    readData[index] = readData[index][1:]
                if readData[index][0] == "[":
                    readData[index] = readData[index][1:]
                if readData[index][0:2] == " [":
                    readData[index] = readData[index][2:]
                data = readData[index].split(",")

                for i in range(len(data)):
                    if "." in data[i]:
                        data[i] = float(data[i])
                    else:
                        data[i] = int(data[i])
                dataList.append(data)
                
        return dataList 

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

    def saveShape(self, fileName):
        
        self.saveFile = open(fileName, "w")
        print("opened file \"" + fileName + "\"")
        print("content to write:")
        pointList = []
        
        for point in self.points:
            pointList.append(point.coords)
        print(pointList)
        edgeList = []
        
        for edge in self.edges:
            edgeStart = 0
            edgeEnd = 0
            
            for index in range(len(self.points)):
                if self.points[index] == edge.startPoint:
                    edgeStart = index
                if self.points[index] == edge.endPoint:
                    edgeEnd = index
            
            edgeList.append([edgeStart, edgeEnd])
            
        print(edgeList)

        self.saveFile.write(str(pointList) + "\n" + str(edgeList))
        self.saveFile.close()


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

    #changing the focal length using the right mouse button
    def changeFocus(self, event):
        mousePos = self.screen.canvasToXY(event.x, event.y)
        mouseDeltaY = mousePos[1] - self.lastMousePos[1]

        #subtract the mouse y delta so you move the mouse up to zoom in and down to zoom out
        self.fLength -= (mouseDeltaY / self.screen.height) * self.screen.unitSize * self.distance * self.screen.scrollRate
        
        if self.fLength < 0:
            self.fLength = 0

        self.lastMousePos = mousePos
        self.screen.updateScreen()

#constants
PHI = (math.sqrt(5) + 1) / 2

#startup variables (normally 800)
screenWidth = 800
screenHeight = 800

#still learning how to use tkinter
root = tk.Tk()
root.title("3D wireframe renderer")
myCamera = Camera(50,5, m = 1.8)
myScreen = Screen(cam = myCamera, master = root, width = screenWidth, height = screenHeight, bg = "black")

#myCube = Shape(0,0,0, "cube.txt")
#myIco = Shape(0,0,0, "icosahedron.txt")
#myDodeca = Shape(0,0,0, "dodecahedron.txt")
#myOcta = Shape(0,0,0, "octahedron.txt")
#myTetra = Shape(0,0,0, "tetrahedron.txt")
#myRhombic = Shape(0,0,0, "rhombicDodecahedron.txt")
#myTria = Shape(0,0,0, "rhombicTriacontahedron.txt")
#testShape = Shape(0,0,0, "saveTest.txt")

#myScreen.shapeDrawList.append(myCube)
#myScreen.shapeDrawList.append(myIco)
#myScreen.shapeDrawList.append(myDodeca)
#myScreen.shapeDrawList.append(myOcta)
#myScreen.shapeDrawList.append(myTetra)
#myScreen.shapeDrawList.append(myRhombic)
#myScreen.shapeDrawList.append(myTria)
#myScreen.shapeDrawList.append(testShape)

#myTria.saveShape("saveTest.txt")

#ask the user which file they want to load
fileToLoad = input("file name: ")
if "." not in fileToLoad:
    fileToLoad = fileToLoad + ".txt"
displayShape = Shape(0, 0, 0, fileToLoad)
myScreen.shapeDrawList.append(displayShape)

#functions to call when the mouse is pressed or dragged in the graphics window
root.bind("<B1-Motion>", myCamera.moveMouse)
root.bind("<Button-1>", myCamera.mouseDown)
root.bind("<B3-Motion>", myCamera.changeFocus)
root.bind("<Button-3>", myCamera.mouseDown)

myScreen.updateScreen()
myScreen.mainloop()
