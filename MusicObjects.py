import pygame
from numpy import *
STAFFSPACING = 15.0
BLACK = pygame.Color("black")
TYPE_ANY = -1
TYPE_NONE = 0
TYPE_STAFF = 1

NOTE_FILLED = -1
NOTE_EMPTY = -2

class MusicObject:
	def __init__(self,pos):
		self.position = pos
		self.type = TYPE_NONE
	def draw(self,canvas,scale):
		pass
	def resize(self,width,scale):
		pass
	def dist(self,point):
		return sqrt(pow(self.position[0]-point[0],2)+pow(self.position[1]-point[1],2))

class Staff(MusicObject):
	def __init__(self,pos,width):
		MusicObject.__init__(self,pos)
		self.width = width
		self.type = TYPE_STAFF
	def draw(self,canvas,scale):
		for i in [-2,-1,0,1,2]:
			h = (i*STAFFSPACING+self.position[1])*scale
			pygame.draw.line(canvas, BLACK, (0,h), (self.width,h), 1*scale)
	# For staves, the vertical distance is all that matters.
	def dist(self,point):
		return abs(self.position[1]-point[1])
	def which_line(self,y,scale = 1):
		return int(round(2.0*(y - self.position[1])/(STAFFSPACING*scale)))

class Barline(MusicObject):
	def __init__(self,pos):
		MusicObject.__init__(self,pos)

class Note(MusicObject):
	def __init__(self,pos,length,parent = None):
		MusicObject.__init__(self,pos)
		self.length = length
		self.parent = parent
		if parent != None:
			line = parent.which_line(pos[1],1)
			self.position[1] = line
	def draw(self,canvas,scale):
		if self.parent == None:
			if self.length == NOTE_FILLED:
				pygame.draw.circle(canvas,pygame.Color("black"),self.position, 8)
			if self.length == NOTE_EMPTY:
				pygame.draw.circle(canvas,pygame.Color("black"),self.position, 8, 2)
		else:
			x = self.position[0]
			y = self.parent.position[1] + int((STAFFSPACING/2.0)*scale*self.position[1])
			if self.length == NOTE_FILLED:
				pygame.draw.circle(canvas,pygame.Color("black"),[x,y], 8)
			if self.length == NOTE_EMPTY:
				pygame.draw.circle(canvas,pygame.Color("black"),[x,y], 8, 2)

def get_closest(objects,point,type = TYPE_ANY):
	dist = inf
	best = None
	for object in objects:
		if (type == TYPE_ANY or object.type == type) and object.dist(point) < dist:
			dist = object.dist(point)
			best = object
	return best
		
