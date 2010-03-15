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
TYPE_ACCIDENTAL = 5
# TODO: use __class__ attribute to check instead of TYPE

NOTE_FILLED = -1
NOTE_EMPTY = -2

ACC_FLAT = 0
ACC_SHARP = 1

BARLINE_NORMAL = 1

"""
Note that some variables are preceeded with an underscore.  These,
while not explicitly "private" (not modifiable even by inherited classes) or
"protected" (not supported in python), are intended to only be written to by the
object which they belong to.  If you find yourself needing to modify
one of these private variables, then thought should be put into (a) doing it a
different (and possibly more appropriate) way, or (b) redesigning the structure
of this code so that is allows you to do what you want in a "nice" way.

Similarly, methods proceeded by an underscore should only be called by methods
of that object
"""

class MusicObject:
	"""
	  A base class for musical objects (WITH semantic meaning; i.e., not just a
	  circle, but a note; not just a line, but a stem or a barline).  The
	  base class just acts like a single point with no meaning, and should not
	  be used by itself.
	"""
	def __init__(self):
		self._type = TYPE_NONE
		self._rect = pygame.Rect(0,0,0,0)
		self._parent = None
		self._children = []

	def draw(self,canvas,scale):
		pass

	# TODO: can we get rid of distance functions?
	def dist(self,point):
		return 0

	def removeAt(self,point):
		"""
		  Remove any objects at the given point.  For notes, remove any accents
		  or accidentals associated with them.  For barlines, simply remove the
		  barline.  For stemmed notes: remove only the stem if the point is
		  over the stem, only the note if it is over one note in a multi-note
		  chord (readjusting stem length if necessary), and both if the point
		  is over the notehead on a single note with stem.
	
		  Return value: a tuple, the first element is True if this object should
		  be removed (from parent), and the second is True is some child was
		  removed
		"""
		# First, recursively check all children
		removedChildren = False
		childrenToRemove = []
		for child in self._children:
			remove, removedChild = child.removeAt(point)
			removedChildren = removedChildren or removedChild or remove
			if remove:
				childrenToRemove.append(child)

		# Then, remove any children that should be removed.
		for child in childrenToRemove:
			self._children.remove(child)
			self._adoptFrom(child)

		# Now, deal with self
		remove = False
		if self.intersectPoint(point):
			remove = True
		elif removedChildren:
			self._reorg()

		return remove, removedChildren

	def _adoptFrom(self,oldParent):
		"""
		  This method should be overwritten for any object that should adopt
		  children.  This means it will probably have to be case-by-case.  For
		  example, staves will adopt notes (from stems), but nothing from notes
		"""
		pass

	def _reorg(self):
		"""
		  This method is called at the end of the remove cycle, if it is
		  necessary to reorganize (when children have been removed).
		"""
		pass

	# These methods check for intersections between the object and a point or
	# rectangle
	def intersectPoint(self,point):
		return self._rect.collidepoint(point)

	def intersectRect(self,rect):
		return self._rect.colliderect(rect)

	# The following methods are recursive; i.e., they check all children as well
	def recurseIntersectPoint(self,point):
		if self.intersectPoint(point):
			return True
		for child in self._children:
			if child.recurseIntersectPoint(point):
				return True
		return False

	def recurseIntersectRect(self,rect):
		if self.intersectRect(rect):
			return True
		for child in self._children:
			if child.recurseIntersectRect(rect):
				return True
		return False

	# TODO: does adding an optional "maxdepth" parameter make any sense?
	# Recursively get anything that intersects the given point/rectangle
	def recurseGetIntersectPoint(self,point,type=TYPE_ANY):
		intersectList = []
		if (self._type == type or type == TYPE_ANY) and self.intersectPoint(point):
			intersectList.append(self)
		for child in self._children:
			intersectList += child.recurseGetIntersectPoint(point,type)
		return intersectList

	def recurseGetIntersectRect(self,rect,type=TYPE_ANY):
		intersectList = []
		if (self._type == type or type == TYPE_ANY) and self.intersectRect(rect):
			intersectList.append(self)
		for child in self._children:
			intersectList += child.recurseGetIntersectRect(rect,type)
		return intersectList

	# The following methods return attributes
	def type(self):
		return self._type

# TODO: what about all "_" variables just being read-only?  How about all
# class variables be read-only?  Then we don't have to mess with "_"...

	# TODO: do we even need distance functions?  Should they be recursive?
	# These are utitily functions for the MusicObject to use in its internal
	# methods, i.e. calculating distance
	def _distVertLine(self,point):
		"""
		  This function computes the distance to a vertical line centered at
		  the x position and with top and bottom equal to the object's rect.
		"""
		if self._rect.top <= point[1] <= self._rect.bottom:
			dy = 0
		else:
			dy = min(self._rect.bottom - point[1],self._rect.top - point[1])
		dx = self._position[0]-point[0]
		return sqrt(dx*dx+dy*dy)

class Staff(MusicObject):
	"""
	  Staves are the base object that is drawn on the page.  They contain notes,
	  clefs, and various other musical symbols, and most other markings are
	  descendents of a staff.
	"""
	def __init__(self,width,ypos):
		MusicObject.__init__(self)
		self._yMiddle = ypos
		self._width = width
		self._type = TYPE_STAFF # TODO: is this redundant with the class name?
		height = STAFFSPACING*4.0
		self._rect = pygame.Rect(0,ypos-height/2.0,width,height)

	def draw(self,canvas,scale):
		"""
		  Draw the staff and all its children (notes, barlines, clefs, etc.)
		"""
		# Draw staff
		for i in [-2,-1,0,1,2]:
			h = int((i*STAFFSPACING+self._yMiddle))
			pygame.draw.line(canvas, BLACK, (0,h), (self._width,h), int(1.0))

		# Draw children
		for obj in self._children:
			obj.draw(canvas,scale)

	def dist(self,point):
		"""
		  For staves, "distance" is just the vertical distance to the center
		"""
		return abs(self._yMiddle-point[1])

	def whichLine(self,y):
		"""
		  Returns the closest line to the given point (with zero being the
		  center of the staff)
		"""
		return int(round(2.0*(y - self._yMiddle)/(STAFFSPACING)))

	# TODO: do we need this?  we can access children directly!
	def addObject(self,obj):
		self._children.append(obj)

	# TODO: do we need this?  we can access children directly!
	def addNote(self,obj):
		self._children.append(obj)

	# TODO: do we need this?  we can access children directly!
	def removeChild(self,object):
		self._children.remove(object)

	# TODO: ditto (probably better to have accessors, though, in case we want
	# to always do something when this is called)
	def addChild(self,obj):
		self._children.append(obj)

	def _adoptFrom(self,oldParent):
		if oldParent._type == TYPE_STEM:
			for child in oldParent._children:
				child.stemToStaff()

class Barline(MusicObject):
	def __init__(self,xpos,parent):
		MusicObject.__init__(self)
		self._parent = parent
		# For barlines, the horizontal distance is all that matters
		self._xpos = xpos;
		self._type = TYPE_BARLINE
		self._style = BARLINE_NORMAL
		self._rect = pygame.Rect(xpos-1,self._parent._rect.top,2,STAFFSPACING*4.0)
	def draw(self,canvas,scale):
		x = self._xpos
		t = self._rect.top
		b = self._rect.bottom
		pygame.draw.line(canvas,pygame.Color("black"),(x,t),(x,b),2)

	def dist(self,point):
		"""
		  For barlines, distance is the minimum distance to the barline
		"""
		return self._distVerticalLine(point)

# TODO: recursively setRects if needed

# TODO: finish this class
class Accidental(MusicObject):
	"""
	  The accidental object is a sharp or flat (or perhaps someday double,
	  three quarters, etc.), and should be the child of a note.  It has no
	  position, except that defined by its parent.
	"""
	def __init__(self,parent,style):
		MusicObject.__init__(self)
		self._parent = parent
		self._parent.addChild(self)
		self._type = TYPE_ACCIDENTAL
		self._style = style
		self._setRect()

	def _setRect(self):
		self._rect = self._parent._rect.move(-STAFFSPACING*1.3,0)

	# TODO: make this shorter/prettier
	def draw(self,canvas,scale):
		w = self._rect.w
		h = self._rect.h
		t = self._rect.top
		l = self._rect.left
		b = self._rect.bottom
		r = self._rect.right
		pygame.draw.line(canvas,pygame.Color("black"),(l+w/3.0,t),(l+w/3.0,b),2)
		pygame.draw.line(canvas,pygame.Color("black"),(l+w/1.5,t),(l+w/1.5,b),2)
		pygame.draw.line(canvas,pygame.Color("black"),(l,h/3.0+t),(r,h/3.0+t),2)
		pygame.draw.line(canvas,pygame.Color("black"),(l,h/1.5+t),(r,h/1.5+t),2)

# TODO: should we put each class in its own file?

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

	#TODO: standardize init function param order
	def __init__(self,pos,parent,length):
		MusicObject.__init__(self)
		self._length = length #TODO: call this style, not length!
		self._parent = parent
		self._type = TYPE_NOTE
		if parent._type == TYPE_STAFF:
			self._line = parent.whichLine(pos[1])
		if parent._type == TYPE_STEM:
			self._line = parent.parent.whichLine(pos[1])
		self._xpos = pos[0] # Absolute pos for free, side of stem for stemmed
		self._setRectAndPos()

	def _setRectAndPos(self):
		"""
		  This function, which should be called anytime the note is moved on
		  the page, sets the note's page-rectangle (for collision purposes) and
		  page-coordinate center position
		"""
		if self._parent.type() == TYPE_STAFF:
			self._x = self._xpos
			self._y = self._parent._yMiddle + (STAFFSPACING/2.0)*self._line
		elif self._parent.type() == TYPE_STEM:
			self._x = self._parent._xpos + (STAFFSPACING/2.0)*self._xpos
			self._y = self._parent._parent._yMiddle + (STAFFSPACING/2.0)*self._line
		self._rect = pygame.Rect(self._x-STAFFSPACING/2.0,self._y-STAFFSPACING/2.0,STAFFSPACING,STAFFSPACING)

	def draw(self,canvas,scale):
		if self._parent._type == TYPE_STAFF:
			staffMiddle = self._parent._yMiddle
		elif self._parent._type == TYPE_STEM:
			staffMiddle = self._parent._parent._yMiddle

		if self._length == NOTE_FILLED:
			pygame.draw.circle(canvas,pygame.Color("black"),[int(round(self._x)),int(round(self._y))], int(round(STAFFSPACING/2.0)))
		elif self._length == NOTE_EMPTY:
			pygame.draw.circle(canvas,pygame.Color("black"),[int(round(self._x)),int(round(self._y))], int(round(STAFFSPACING/2.0)), 2)

		# Draw ledger lines if the note is...
		# ...above the staff, or...
		for line in range(int(ceil(self._line/2.))*2,-4,2):
			h = int((staffMiddle+(line/2)*STAFFSPACING)*scale)
			pygame.draw.line(canvas, BLACK, (self._x-(STAFFSPACING/1.5)*scale,h), (self._x+(STAFFSPACING/1.5),h), int(1.0))
		# below the staff
		for line in range(6,int(self._line/2)*2+2,2):
			h = int((staffMiddle+(line/2)*STAFFSPACING)*scale)
			pygame.draw.line(canvas, BLACK, (self._x-(STAFFSPACING/1.5)*scale,h), (self._x+(STAFFSPACING/1.5),h), int(1.0))

		for child in self._children:
			child.draw(canvas,scale)

	def dist(self,point):
		"""
		  The distance function here will return the distance, in page
		  coordinates, to the edge of the note
		"""
		x = self._x-point[0]
		y = self._y-point[1]
		return max(sqrt(x*x+y*y)-STAFFSPACING/2.0,0)

# TODO: add adopts (for staff)
# TODO: cleanup stem lenght


	def intersectPoint(self,point):
		return self.dist(point) == 0

	def staffToStem(self,stem):
		"""
		  NOTE: called by stem only
		"""
		# reset x-position
		self._xpos = -stem.isStemUp()

		# change ownership (already owned by stem who called this)
		self._parent.removeChild(self)
		self._parent = stem

		# Adjust rectangle and position
		self._setRectAndPos()

	def stemToStaff(self):
		# reset x-position (absolute instead of side)
		self._xpos = self._parent._xpos + (STAFFSPACING/2.0)*self._xpos;

		# change ownership (owned by no-one)
		self._parent = self._parent._parent
		self._parent.addChild(self)

		# Adjust rectangle and position
		self._setRectAndPos()

	def setSide(self,side):
		"""
		  If the note's parent is a stem, set which side of the stem it is on.
		  This method should not be called if the parent is not a stem.
		"""
		# TODO: debug here: if we not parented by a stem, say something
		self._xpos = side

		# Adjust rectangle and position
		self._setRectAndPos()

#	def removeAt(self,point):
#		removeMe = []
#		for child in self._children:
#			if child.intersectPoint(point):
#				removeMe.append(child)

#		for child in removeMe:
#			self._children.remove(child)

#		if self.intersectPoint(point):
#			print "note needs to die!"

	def addChild(self,child):
		self._children.append(child)

# TODO: remove commented functions!

# TODO: figure out how to handle removals in thie hierarchy!

# TODO: when recursively removing, don't remove yourself from parent -- it might be removing from a list while looping through.  Is this ok?  Is there a better way?

# TODO: standard function order?

# TODO: debug warnings?

# TODO: change all comments? shorter style?

# TODO: consider eliminating position, and just using rectangle center?

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
		MusicObject.__init__(self)
		# -1 represents a down stem, +1 represents an up stem. 
		self._direction = direction
		# The length of the stem, in number of lines and spaces
		self._length = length
		# The note or notes that this stem attaches to.
		self._children = children
		# The parent staff which this stem belongs to.
		self._parent = parent
		self._type = TYPE_STEM
		self._xpos = pos[0]
		self._baseLine = pos[1]

		for note in self._children:
			note.staffToStem(self)

		self._setRect()
		self._clusterNotes()

	# TODO: change all xpos and ypos to xPos and yPos? consistency!

	def _setRect(self):
		x = self._xpos
		yTop = self._parent._yMiddle + int((STAFFSPACING/2.0)*self._baseLine)
		yBot = yTop
		if self._direction == 1:
			yTop -= self._length*STAFFSPACING/2.0
		else:
			yBot += self._length*STAFFSPACING/2.0
		self._rect = pygame.Rect(x-1,yTop,2,yBot-yTop)

	def addNotes(self,children):
		for note in children:
			self._children.append(note)
			note.staffToStem(self)

		self._clusterNotes()

	def draw(self,canvas,scale):
		for note in self._children:
			note.draw(canvas,scale)
		x = self._xpos
		t = self._rect.top
		b = self._rect.bottom
		pygame.draw.line(canvas,pygame.Color("black"),(x,t),(x,b),2)

	def dist(self,point):
		"""
		  The distance function here will return the distance, in page
		  coordinates, to the closest part of the stem.
		"""
		return self._distVertLine()

	# TODO: think about removeAt hierarchy
#	def removeAt(self,point):
#		"""
#		  This is called if a stem or stemmed note collides with the given point
#		  and has to be removed.
#		"""
#		removeMe = []
#		for note in self._children:
#			if note.intersectPoint(point):
#				removeMe.append(note)
#		for note in removeMe:
#			self._children.remove(note)

#		for note in self._children:
#			note.removeAt(point)

		# If we collide with the stem or have erased all the notes, delete the
		# stem
#		if self.intersectPoint(point) or len(self._children) == 0:
#			self._parent.objects.removeChild(self)
#			for note in self._children:
#				note.stemToStaff()
				# We do not need to delete the note from _children, because
				# the stem is about to be deleted

		# recompute stem location, length, and any clusters
		"""		else:
			# the base note is the lowest on the page (highest y)
			if self._direction == 1:
				maxPos = -inf
				for note in self._children:
					maxPos = max(note._line,maxPos)
				self._length -= self._baseLine-maxPos
				self._baseLine = maxPos
			# the base note is the highest on the page (lowest y)
			else:
				minPos = inf
				for note in self._children:
					minPos = min(note._line,minPos)
				self._length -= minPos-self._baseLine
				self._baseLine = minPos
			#clusters the remaining notes correctly
			self._clusterNotes()"""

	# TODO: move from bottom and top line rather than base and length?

	# TODO: perhaps make this function shorter
	def _clusterNotes(self):
		"""
			This function computes the correct x-position (left or right of the
			stem) for each note in a chord, taking into account the effect of
			"clustered" notes (ones a second apart)
		"""
		noteList = {}
		for note in self._children:
			noteList[note._line] = note
		order = noteList.keys()
		order.sort()
		# TODO: do this ordering elsewhere, only when appropriate, and then
		# have children always in order?

		# For a down-stem:
		if self._direction == -1:
			noteList[order[0]].setSide(-self._direction)
			for i in range(1,len(order)):
				if (order[i-1] == order[i]-1):
					noteList[order[i]].setSide(-noteList[order[i-1]]._xpos)
				else:
					noteList[order[i]].setSide(-self._direction)
		# For an up-stem:
		else:
			noteList[order[-1]].setSide(-self._direction)
			for i in range(1,len(order)):
				if (order[-i] == order[-i-1]+1):
					noteList[order[-i-1]].setSide(-noteList[order[-i]]._xpos)
				else:
					noteList[order[-i-1]].setSide(-self._direction)

	def isStemUp(self):
		return self._direction

#TODO: consider eliminating these

#def getClosest(objects,point,type = TYPE_ANY):
#	dist = inf
#	best = None
#	for object in objects:
#		if (type == TYPE_ANY or object.type == type) and object.dist(point) < dist:
#			dist = object.dist(point)
#			best = object
#	return best, dist

def getClosestStaff(staves,point):
	dist = inf
	best = None
	for staff in staves:
		if staff.dist(point) < dist:
			dist = staff.dist(point)
			best = staff
	return best, dist
	

#def getObjectsIn(objects,rect,type = TYPE_ANY):
#	"""
#	  Return all objects of a given type that are in the given rectangle.
#	"""
#	inside = []
#	for object in objects:
#		if (type == TYPE_ANY or object.type == type) and object.isIn(rect):
#			inside.append(object)
#	return inside
