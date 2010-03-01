import pygame
from numpy import *
STAFFSPACING = 15.0
BLACK = pygame.Color("black")
TYPE_ANY = -1
TYPE_NONE = 0
TYPE_STAFF = 1
TYPE_NOTE = 2
TYPE_BARLINE = 3
TYPE_STEM = 4

NOTE_FILLED = -1
NOTE_EMPTY = -2

BARLINE_NORMAL = 1

class MusicObject:
	"""
	  A base class for musical objects (WITH semantic meaning; i.e., not just a
	  circle, but a note; not just a line, but a stem or a barline).  The
	  base class just acts like a single point with no meaning, and should not
	  be used by itself.
	"""
	def __init__(self,pos):
		self.position = list(pos)
		self.type = TYPE_NONE
	def draw(self,canvas,scale):
		pass
	def dist(self,point):
		return sqrt(pow(self.position[0]-point[0],2)+pow(self.position[1]-point[1],2))
	def dist2(self,point):
		"""
		  Returns the horizontal and vertical distances from the object to the
		  given point.  Should return signed distances.
		"""
		return [self.position[0]-points[0],self.position[1]-point[1]]
	def isUnder(self,point):
		"""
		  This function determines whether the given point is over the object,
		  which is useful, for example, in determining whether to erase it.
		"""
		return False
	def isIn(self,rect):
		"""
		  This functions returns 1 if some part of the object is within the
		  given rectangle.
		"""
		return (rect[0][0] < self.position[0] < rect[1][0]) and (rect[0][1] < self.position[1] < rect[1][1])

class Staff(MusicObject):
	"""
	  Staves are the base object that is drawn on the page.  They contain notes,
	  clefs, and various other musical symbols, and most other markings are
	  children of a staff.
	"""
	def __init__(self,pos,width):
		MusicObject.__init__(self,pos)
		self.width = width
		self.type = TYPE_STAFF
		self.objects = []

	def draw(self,canvas,scale):
		"""
		  Draw the staff and all its children (notes, barlines, clefs, etc.)
		"""
		# Draw staff
		for i in [-2,-1,0,1,2]:
			h = int((i*STAFFSPACING+self.position[1])*scale)
			pygame.draw.line(canvas, BLACK, (0,h), (self.width,h), int(1.0*scale))
		# Draw children
		for obj in self.objects:
			obj.draw(canvas,scale)

	# For staves, "distance" is just the vertical distance to the center
	def dist(self,point):
		return abs(self.position[1]-point[1])

	def dist2(self,points):
		return [0,self.position[1]-point[1]]

	# This function returns the closest line the the given point (with zero
	# being the center of the staff)
	def whichLine(self,y):
		return int(round(2.0*(y - self.position[1])/(STAFFSPACING)))

	# These remaining functions add notes and other objects to the list of
	# children of the staff.
	def addNote(self,note):
		self.objects.append(note)
	def addObject(self,obj):
		self.objects.append(obj)

class Barline(MusicObject):
	def __init__(self,xpos,parent):
		MusicObject.__init__(self,(xpos,0))
		self.parent = parent
		# For barlines, the horizontal distance is all that matters
		self.position = (xpos,0);
		self.type = TYPE_BARLINE
		self.style = BARLINE_NORMAL
	def draw(self,canvas,scale):
		x = self.position[0]
		t = self.parent.position[1] + int((STAFFSPACING/2.0)*scale*(-4))
		b = self.parent.position[1] + int((STAFFSPACING/2.0)*scale*(4))
		pygame.draw.line(canvas,pygame.Color("black"),(x,t),(x,b),2)
	# For barlines, distance is the horizontal distance to the line
	def dist(self,point):
		return abs(self.position[0]-point[0])

class Note(MusicObject):
	"""
	  The notehead object represents a single notehead.  It's parent is either a
	  stem or a staff.

	  When the parent is a staff, the note is a "free" note.  The x position is
	  the position from the left side of the page,
	
	  When the parent is a stem, the note is attached to that stem (possibly
	  with other notes).  The x position now is either -1, to represent
	  attachment to the left side of the stem, or +1, to represent attachement
	  to the right side of the stem.
	
	  In either case, the y position is the line or space number of the staff
	  that is either its parent or grandparent.
	"""
	def __init__(self,pos,parent,length,side=-1):
		MusicObject.__init__(self,pos)
		self.length = length
		self.parent = parent
		self.type = TYPE_NOTE
		if self.parent.type == TYPE_STAFF:
			self.position[1] = parent.whichLine(pos[1])
		if self.parent.type == TYPE_STEM:
			self.position[1] = parent.parent.whichLine(pos[1])
			self.position[0] = side

	def draw(self,canvas,scale):
		"""
		  Because the x and y positions have different semantic meanings if the
		  parent is a staff or a stem, these cases are handled differently here.
		"""
		if self.parent.type == TYPE_STAFF:
			x = int(self.position[0])
			y = self.parent.position[1] + int((STAFFSPACING/2.0)*scale*self.position[1])
			staffMiddle = self.parent.position[1]
		elif self.parent.type == TYPE_STEM:
			side = self.position[0]
			x = int(self.parent.position[0] + (STAFFSPACING/2.0)*scale*side);
			y = self.parent.parent.position[1] + int((STAFFSPACING/2.0)*scale*self.position[1])
			staffMiddle = self.parent.parent.position[1]

		if self.length == NOTE_FILLED:
			pygame.draw.circle(canvas,pygame.Color("black"),[x,y], 8)
		elif self.length == NOTE_EMPTY:
			pygame.draw.circle(canvas,pygame.Color("black"),[x,y], 8, 2)

		# Draw ledger lines if the note is...
		# ...above the staff, or...
		for line in range(int(ceil(self.position[1]/2.))*2,-4,2):
			h = int((staffMiddle+(line/2)*STAFFSPACING)*scale)
			pygame.draw.line(canvas, BLACK, (x-(STAFFSPACING/1.5)*scale,h), (x+(STAFFSPACING/1.5),h), int(1.0*scale))
		# below the staff
		for line in range(6,int(self.position[1]/2)*2+2,2):
			h = int((staffMiddle+(line/2)*STAFFSPACING)*scale)
			pygame.draw.line(canvas, BLACK, (x-(STAFFSPACING/1.5)*scale,h), (x+(STAFFSPACING/1.5),h), int(1.0*scale))

	def dist(self,point):
		"""
		  The distance function here will return the distance, in page
		  coordinates, to the center of the note.
		"""
		x = self.position[0]-point[0]
		y = self.parent.position[1] + int((STAFFSPACING/2.0)*self.position[1]) - point[1]
		return sqrt(x*x+y*y)
	def isUnder(self,point):
		return self.dist(point) < (STAFFSPACING/2.0)
	def isIn(self,rect):
		"""
		  This is actually just a (close) approximation, for computational
		  efficiency.  To figure out whether an object is in another, you can
		  check whether a point is in the minkowski sum.  In this case, we
		  instead just expand the rectangle by the note radius, and check the
		  center position of the note, which gives (a small number of) false
		  positives at the corners.
		"""
		# Get x and y in page coordinates		
		if self.parent.type == TYPE_STAFF:
			x = int(self.position[0])
			y = self.parent.position[1] + int((STAFFSPACING/2.0)*self.position[1])
		elif self.parent.type == TYPE_STEM:
			side = self.position[0]
			x = int(self.parent.position[0] + (STAFFSPACING/2.0)*side);

		return ((rect[0][0]-STAFFSPACING*0.5) < x < (rect[1][0]+STAFFSPACING*0.5)) and ((rect[0][1]-STAFFSPACING*0.5) < y < (rect[1][1]+STAFFSPACING*0.5))

# This is a stem for a notehead.  It's parent is the chord it attaches to.
class Stem(MusicObject):
	"""
	  A stem is a vertical line, attached to one or more notes.  It can either
	  be pointing up from the bottom note of the chord, on the right side
	  (except for clusters), or can be pointing down from the top note of the
	  chord, on the left side (again, note clusters must be handled as a
	  special case).

	  The x and y position coordinates act like free notes; in other words, the
	  x position is the page coordinate of the stem, from the left side of the
	  page, and the y position is the line or space at which the stem begins.
	"""
	def __init__(self,pos,parent,length,direction,children):
		MusicObject.__init__(self,pos)
		# -1 represents a down stem, +1 represents an up stem. 
		self.direction = direction
		# The length of the stem, in number of lines and spaces
		self.length = length
		# The note or notes that this stem attaches to.
		self.notes = children
		# The parent staff which this stem belongs to.
		self.parent = parent
		self.type = TYPE_STEM

		# During initialization, the stem must set parameters of its new
		# children, and remove them from the staff's set of children
		for note in self.notes:
			# Set the x position of the notes.  In general, this is the left
			# side for up-stems, and the left side for down-stems.
			#TODO figure out logic for determing stem side for clusters of notes
			note.position[0] = -self.direction

			# Remove the note from its parent staff
			note.parent.objects.remove(note)

			# Change the note's parent to this stem
			note.parent = self

	def addNotes(self,notes):
		for note in notes:
			# Add new notes to the stem's list of notes, and remove from the
			# list of their previous parent
			self.notes.append(note)
			note.parent.objects.remove(note)

			# Set the x position of the notes.  In general, this is the left
			# side for up-stems, and the left side for down-stems.
			note.position[0] = -self.direction

			# Change the note's parent to this stem
			note.parent = self

	def draw(self,canvas,scale):
		for note in self.notes:
			note.draw(canvas,scale)
		x = self.position[0]
		line = self.position[1]
		base = self.parent.position[1] + int((STAFFSPACING/2.0)*scale*(line))
		end = base-scale*STAFFSPACING/2.0*self.length*self.direction
		pygame.draw.line(canvas,pygame.Color("black"),(x,base),(x,end),2)

	def dist(self,point):
		"""
		  The distance function here will return the distance, in page
		  coordinates, to the closest part of the stem.
		"""
		x = self.position[0]-point[0]
		yTop = self.parent.position[1] + int((STAFFSPACING/2.0)*self.position[1])
		yBot = yTop
		if self.direction == 1:
			yTop -= self.length*STAFFSPACING/2.0
		else:
			yBot += self.length*STAFFSPACING/2.0
		if yTop < point[1] < yBot:
			y = 0
		else:
			y = min(abs(point[1] - yTop),abs(point[1] - yBot))

		return sqrt(x*x+y*y)

def getClosest(objects,point,type = TYPE_ANY):
	dist = inf
	best = None
	for object in objects:
		if (type == TYPE_ANY or object.type == type) and object.dist(point) < dist:
			dist = object.dist(point)
			best = object
	return best, dist

def getObjectsIn(objects,rect,type = TYPE_ANY):
	"""
	  Return all objects of a given type that are in the given rectangle.
	"""
	inside = []
	for object in objects:
		if (type == TYPE_ANY or object.type == type) and object.isIn(rect):
			inside.append(object)
	return inside
