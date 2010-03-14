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

ACC_FLAT = 0
ACC_SHARP = 1

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
		self.rect = pygame.Rect(0,0,0,0)
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
		height = STAFFSPACING*4.0
		self.rect = pygame.Rect(pos[0],pos[1]-height/2.0,width,height)

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

	def removeAt(self,point):
		"""
		  Remove any objects at the given point.  For notes, remove any accents
		  or accidentals associated with them.  For barlines, simply remove the
		  barline.  For stemmed notes: remove only the stem if the point is
		  over the stem, only the note if it is over one note in a multi-note
		  chord (readjusting stem length if necessary), and both if the point
		  is over the notehead on a single note with stem.
	
		  Return value is True if objects were removed, false if not.
		"""
		removed = False
		for object in self.objects:
			if object.isUnder(point):
				# Remove free notes and barlines
				if object.type == TYPE_NOTE or object.type == TYPE_BARLINE:
					self.objects.remove(object)
					removed = True
				# Remove notes from stem or stem from notes (or both)
				if object.type == TYPE_STEM:
					object.removeAt(point)
					removed = True
		return removed

class Barline(MusicObject):
	def __init__(self,xpos,parent):
		MusicObject.__init__(self,(xpos,0))
		self.parent = parent
		# For barlines, the horizontal distance is all that matters
		self.position = (xpos,0);
		self.type = TYPE_BARLINE
		self.style = BARLINE_NORMAL
		self.rect = pygame.Rect(xpos-1,self.parent.rect.top,2,self.parent.rect.h)
	def draw(self,canvas,scale):
		x = self.position[0]
		t = self.parent.position[1] + int((STAFFSPACING/2.0)*scale*(-4))
		b = self.parent.position[1] + int((STAFFSPACING/2.0)*scale*(4))
		pygame.draw.line(canvas,pygame.Color("black"),(x,t),(x,b),2)
	# For barlines, distance is the horizontal distance to the line
	def dist(self,point):
		return abs(self.position[0]-point[0])
	def isUnder(self,point):
		return self.rect.collidepoint(point)

class Accidental(MusicObject):
	"""
	  The accidental object is a sharp or flat (or perhaps someday double,
	  three quarters, etc.), and should be the child of a note.  It has no
	  position, except that defined by its parent.
	"""
	def __init__(self,parent,type):
		MusicObject.__init__(self,(0,0))
		self.parent = parent
		self.type = type
		self.setRect()

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
		self.setRect()
		self.children = []

	def setRect(self):
		if self.parent.type == TYPE_STAFF:
			x = self.position[0]
			y = self.parent.position[1] + (STAFFSPACING/2.0)*self.position[1]
		elif self.parent.type == TYPE_STEM:
			side = self.position[0]
			x = self.parent.position[0] + (STAFFSPACING/2.0)*scale*side;
			y = self.parent.parent.position[1] + (STAFFSPACING/2.0)*self.position[1]
		self.rect = pygame.Rect(x-STAFFSPACING/2.0,y-STAFFSPACING/2.0,STAFFSPACING,STAFFSPACING)

	def draw(self,canvas,scale):
		"""
		  Because the x and y positions have different semantic meanings if the
		  parent is a staff or a stem, these cases are handled differently here
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

		for child in self.children:
			child.draw(canvas,scale)

	def dist(self,point):
		"""
		  The distance function here will return the distance, in page
		  coordinates, to the center of the note.
		"""
		if self.parent.type == TYPE_STAFF:
			x = self.position[0]-point[0]
			y = self.parent.position[1] + (STAFFSPACING/2.0)*self.position[1]-point[1]
		elif self.parent.type == TYPE_STEM:
			side = self.position[0]
			x = int(self.parent.position[0] + (STAFFSPACING/2.0)*side)-point[0]
			y = self.parent.parent.position[1] + (STAFFSPACING/2.0)*self.position[1]-point[1]
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
			y = self.parent.parent.position[1] + int((STAFFSPACING/2.0)*self.position[1])

		return ((rect[0][0]-STAFFSPACING*0.5) < x < (rect[1][0]+STAFFSPACING*0.5)) and ((rect[0][1]-STAFFSPACING*0.5) < y < (rect[1][1]+STAFFSPACING*0.5))

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
		self.setRect()
		self.clusterNotes()

	def setRect(self):
		x = self.position[0]
		yTop = self.parent.position[1] + int((STAFFSPACING/2.0)*self.position[1])
		yBot = yTop
		if self.direction == 1:
			yTop -= self.length*STAFFSPACING/2.0
		else:
			yBot += self.length*STAFFSPACING/2.0
		self.rect = pygame.Rect(x-1,yTop,2,yBot-yTop)

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
		self.clusterNotes()

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

	def isUnder(self,point):
		"""
		  Is any part of the stem or connected notes under the given point?
		"""
		if self.rect.collidepoint(point):
			return True
		for note in self.notes:
			if note.isUnder(point):
				return True
		return False

	def removeAt(self,point):
		"""
		  This is called if a stem or stemmed note collides with the given point
		  and has to be removed.
		"""
		removeMe = []
		for note in self.notes:
			if note.isUnder(point):
				removeMe.append(note)
		for note in removeMe:
			self.notes.remove(note)

		# If we collide with the stem or have erased all the notes, delete the
		# stem
		if self.rect.collidepoint(point) or len(self.notes) == 0:
			self.parent.objects.remove(self)
			for note in self.notes:
				self.parent.objects.append(note)
				note.parent = self.parent
				note.position[0] = self.position[0] + (STAFFSPACING/2.0)*note.position[0];
		# recompute stem location, length, and any clusters
		else:
			# the base note is the lowest on the page (highest y)
			if self.direction == 1:
				maxPos = -inf
				for note in self.notes:
					maxPos = max(note.position[1],maxPos)
				self.length -= self.position[1]-maxPos
				self.position[1] = maxPos
			# the base note is the highest on the page (lowest y)
			else:
				minPos = inf
				for note in self.notes:
					minPos = min(note.position[1],minPos)
				self.length -= minPos-self.position[1]
				self.position[1] = minPos
			#clusters the remaining notes correctly
			self.clusterNotes()

	def clusterNotes(self):
		"""
			This function computes the correct x-position (left or right of the
			stem) for each note in a chord, taking into account the effect of
			"clustered" notes (ones a second apart)
		"""
		noteList = {}
		for note in self.notes:
			noteList[note.position[1]] = note
		order = noteList.keys()
		order.sort()

		# For a down-stem:
		if self.direction == -1:
			noteList[order[0]].position[0] = -self.direction
			for i in range(1,len(order)):
				if (order[i-1] == order[i]-1):
					noteList[order[i]].position[0] = -noteList[order[i-1]].position[0]
				else:
					noteList[order[i]].position[0] = -self.direction
		# For an up-stem:
		else:
			noteList[order[-1]].position[0] = -self.direction
			for i in range(1,len(order)):
				if (order[-i] == order[-i-1]+1):
					noteList[order[-i-1]].position[0] = -noteList[order[-i]].position[0]
				else:
					noteList[order[-i-1]].position[0] = -self.direction

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
