import pygame
from numpy import *
STAFFSPACING = 15.0
MINSTEMLENGTH = 6 # minimum stem length, in lines and spaces.

BLACK = pygame.Color("black")
TYPE_ANY = -1

NOTE_FILLED = -1
NOTE_EMPTY = -2

# Accidentals, Accents, and other note additions
ACC_FLAT = -1
ACC_NATURAL = 0
ACC_SHARP = 1
ACC_RHYTHM_DOT = 2

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
of that object.

There is a standard parameter order for initializers of MusicObjects.  Some of
these are optional, depending on the object. The order is:
  self
  parent
  position (this could be one or two elements; a single element represents a
            page position, while two represents something more independent (such
            as a width and a page height, or an page x position and a line
            number)
  size
  style/type/etc
  children

Finally, there is a standard order of functions (for readability):
  Basic Functions:
    __init__
	addChild
    draw
  Distance: TODO: MAYBE REMOVE THESE FUNCTIONS!
    dist
    _distVertLine
  Intersection:
    intersectPoint
    intersectRect
    recurseIntersectPoint
    recurseIntersectRect
    recurseGetIntersectPoint
    recurseGetIntersectRect
	setRect
  Removal:
    removeAt
    _adoptFrom
    _reorg
  Other:
    _cantSurviveWithoutChildren
    (any other functions that apply to this object, such as attribute modifiers)
"""

class MusicObject:
	"""
	  A base class for musical objects (WITH semantic meaning; i.e., not just a
	  circle, but a note; not just a line, but a stem or a barline).  The
	  base class just acts like a single point with no meaning, and should not
	  be used by itself.
	"""
	def __init__(self,parent):
		self._rect = pygame.Rect(0,0,0,0)
		self._parent = parent
		self._children = []
		# Since the highest level objects have "None" type parent, this
		# prevents errors.
		if self._parent:
			self._parent.addChild(self)

	def addChild(self,obj):
		"""
		  This should be overwritten if the object should do something special
		  when a child is added (such as recompute clusters, stem length, etc)
		"""
		self._children.append(obj)

	def draw(self,canvas,scale):
		pass

	def dist(self,point):
		return 0

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

	# Recursively get anything that intersects the given point/rectangle
	def recurseGetIntersectPoint(self,point,type=TYPE_ANY):
		intersectList = []
		if (self.__class__ == type or type == TYPE_ANY) and self.intersectPoint(point):
			intersectList.append(self)
		for child in self._children:
			intersectList += child.recurseGetIntersectPoint(point,type)
		return intersectList

	def recurseGetIntersectRect(self,rect,type=TYPE_ANY):
		intersectList = []
		if (self.__class__ == type or type == TYPE_ANY) and self.intersectRect(rect):
			intersectList.append(self)
		for child in self._children:
			intersectList += child.recurseGetIntersectRect(rect,type)
		return intersectList

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
		# Can't survive without children?
		if self.intersectPoint(point) or (len(self._children) == 0 and self._cantSurviveWithoutChildren()):
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

	def _cantSurviveWithoutChildren(self):
		"""
		  This is a property of the particular class -- i.e., whether or not
		  it should be removed when its children are all gone.
		"""
		return False

class Staff(MusicObject):
	"""
	  Staves are the base object that is drawn on the page.  They contain notes,
	  clefs, and various other musical symbols, and most other markings are
	  descendents of a staff.
	"""
	def __init__(self,parent,width,yPos):
		MusicObject.__init__(self,parent)
		self._yMiddle = yPos
		self._width = width
		height = STAFFSPACING*4.0
		self._rect = pygame.Rect(0,yPos-height/2.0,width,height)

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

	def _adoptFrom(self,oldParent):
		if oldParent.__class__ == Stem:
			for child in oldParent._children:
				child.stemToStaff()

	def removeChild(self,obj):
		self._children.remove(obj)

	def whichLine(self,y):
		"""
		  Returns the closest line to the given point (with zero being the
		  center of the staff)
		"""
		return int(round(2.0*(y - self._yMiddle)/(STAFFSPACING)))

class Barline(MusicObject):
	def __init__(self,parent,xPos):
		MusicObject.__init__(self,parent)
		self._parent = parent
		# For barlines, the horizontal position is all that matters
		self._xPos = xPos;
		self._style = BARLINE_NORMAL
		self._rect = pygame.Rect(xPos-1,self._parent._rect.top,2,STAFFSPACING*4.0)
	def draw(self,canvas,scale):
		x = self._xPos
		t = self._rect.top
		b = self._rect.bottom
		pygame.draw.line(canvas,pygame.Color("black"),(x,t),(x,b),2)

	def dist(self,point):
		"""
		  For barlines, distance is the minimum distance to the barline
		"""
		return self._distVerticalLine(point)

class Accent(MusicObject):
	def __init__(self,parent,style):
		MusicObject.__init__(self,parent)
		self._parent = parent
		self._style = style
		self._setRect()

	def draw(self,canvas,scale):
		if self._style == ACC_RHYTHM_DOT:
			pygame.draw.circle(canvas,pygame.Color("black"),[int(round(self._rect.centerx)),int(round(self._rect.centery))], int(round(0.1*STAFFSPACING/2.0)))

	def _setRect(self):
		if self._style == ACC_RHYTHM_DOT:
			self._rect = self._parent._rect.move(STAFFSPACING*1,0)
			self._rect.inflate_ip(-self._rect.w*0.9,-self._rect.h*0.9)

	def move(self):
		"""
		  This function gets called when something above in the heirarchy has
		  been moved.
		"""
		self._setRect()

class Accidental(MusicObject):
	"""
	  The accidental object is a sharp/flat/natural (or perhaps someday double,
	  three quarters, etc.), and should be the child of a note.  It has no
	  position, except that defined by its parent.
	"""
	def __init__(self,parent,style):
		MusicObject.__init__(self,parent)
		self._parent = parent
		self._style = style
		self._setRect()

	def draw(self,canvas,scale):
		if self._style == ACC_SHARP:
			# Vertical lines
			pygame.draw.line(canvas,pygame.Color("black"),(self._rect.left+self._rect.w*0.33,self._rect.top),(self._rect.left+self._rect.w*0.33,self._rect.bottom),2)
			pygame.draw.line(canvas,pygame.Color("black"),(self._rect.left+self._rect.w*0.66,self._rect.top),(self._rect.left+self._rect.w*0.66,self._rect.bottom),2)
			# Horizontal lines
			pygame.draw.line(canvas,pygame.Color("black"),(self._rect.left,self._rect.h*0.40+self._rect.top),(self._rect.right,self._rect.w*0.26+self._rect.top),2)
			pygame.draw.line(canvas,pygame.Color("black"),(self._rect.left,self._rect.h*0.73+self._rect.top),(self._rect.right,self._rect.w*0.59+self._rect.top),2)
		elif self._style == ACC_FLAT:
			pygame.draw.line(canvas,pygame.Color("black"),(self._rect.left,self._rect.top),(self._rect.left,self._rect.bottom),2)
			pygame.draw.arc(canvas,pygame.Color("black"),pygame.Rect(self._rect.left-self._rect.w,self._rect.top+self._rect.h*0.34,self._rect.w*2.0,self._rect.h*0.68),-pi/2,0,2)
			pygame.draw.arc(canvas,pygame.Color("black"),pygame.Rect(self._rect.left-self._rect.w/3.0,self._rect.top+self._rect.h*0.5,self._rect.w*4.0/3.0,self._rect.h*0.34),0,pi/2,2)
			pygame.draw.line(canvas,pygame.Color("black"),(self._rect.left,self._rect.top+self._rect.h*0.67),(self._rect.left+self._rect.w/3.0,self._rect.top+self._rect.h/2.0),2)
		elif self._style == ACC_NATURAL:
			pygame.draw.line(canvas,pygame.Color("black"),(self._rect.left,self._rect.top),(self._rect.left,self._rect.top+self._rect.h*0.7),1)
			pygame.draw.line(canvas,pygame.Color("black"),(self._rect.right,self._rect.top+self._rect.h*0.3),(self._rect.right,self._rect.bottom),1)
			pygame.draw.line(canvas,pygame.Color("black"),(self._rect.left,self._rect.top+self._rect.h*0.4),(self._rect.right,self._rect.top+self._rect.h*0.2),3)
			pygame.draw.line(canvas,pygame.Color("black"),(self._rect.left,self._rect.top+self._rect.h*0.8),(self._rect.right,self._rect.top+self._rect.h*0.6),3)

	def _setRect(self):
		if self._style == ACC_SHARP:
			self._rect = self._parent._rect.move(-STAFFSPACING*1.3,0)
		elif self._style == ACC_FLAT:
			self._rect = self._parent._rect.move(-STAFFSPACING*1.3,-STAFFSPACING*0.4)
			self._rect.inflate_ip(0,self._rect.h*0.8)
		elif self._style == ACC_NATURAL:
			self._rect = self._parent._rect.move(-STAFFSPACING*1.1,0)
			self._rect.inflate_ip(-self._rect.w*0.6,self._rect.h)

	def move(self):
		"""
		  This function gets called when something above in the heirarchy has
		  been moved.
		"""
		self._setRect()

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

	def __init__(self,parent,pos,style):
		MusicObject.__init__(self,parent)
		self._style = style
		self._parent = parent
		if parent.__class__ == Staff:
			self._line = parent.whichLine(pos[1])
		if parent.__class__ == Stem:
			self._line = parent.parent.whichLine(pos[1])
		self._xPos = pos[0] # Absolute pos for free, side of stem for stemmed
		self._setRectAndPos()

	def draw(self,canvas,scale):
		if self._parent.__class__ == Staff:
			staffMiddle = self._parent._yMiddle
		elif self._parent.__class__ == Stem:
			staffMiddle = self._parent._parent._yMiddle

		if self._style == NOTE_FILLED:
			pygame.draw.circle(canvas,pygame.Color("black"),[int(round(self._x)),int(round(self._y))], int(round(STAFFSPACING/2.0)))
		elif self._style == NOTE_EMPTY:
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

	def intersectPoint(self,point):
		return self.dist(point) == 0

	def _setRectAndPos(self):
		"""
		  This function, which should be called anytime the note is moved on
		  the page, sets the note's page-rectangle (for collision purposes) and
		  page-coordinate center position
		"""
		if self._parent.__class__ == Staff:
			self._x = self._xPos
			self._y = self._parent._yMiddle + (STAFFSPACING/2.0)*self._line
		elif self._parent.__class__ == Stem:
			self._x = self._parent._xPos + (STAFFSPACING/2.0)*self._xPos
			self._y = self._parent._parent._yMiddle + (STAFFSPACING/2.0)*self._line
		self._rect = pygame.Rect(self._x-STAFFSPACING/2.0,self._y-STAFFSPACING/2.0,STAFFSPACING,STAFFSPACING)

		for child in self._children:
			child.move()

	def staffToStem(self,stem):
		"""
		  NOTE: called by stem only
		"""
		# reset x-position
		self._xPos = -stem.isStemUp()

		# change ownership (already owned by stem who called this)
		self._parent.removeChild(self)
		self._parent = stem

		# Adjust rectangle and position
		self._setRectAndPos()

	def stemToStaff(self):
		# reset x-position (absolute instead of side)
		self._xPos = self._parent._xPos + (STAFFSPACING/2.0)*self._xPos;

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
		self._xPos = side

		# Adjust rectangle and position
		self._setRectAndPos()

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
	def __init__(self,parent,pos,length,direction,children):
		MusicObject.__init__(self,parent)
		# -1 represents a down stem, +1 represents an up stem. 
		self._direction = direction
		# The length of the stem, in number of lines and spaces
		self._length = length
		# The note or notes that this stem attaches to.
		self._children = children
		# The parent staff which this stem belongs to.
		self._parent = parent
		self._xPos = pos[0]
		self._baseLine = pos[1]

		for note in self._children:
			note.staffToStem(self)

		self._orderNotes()
		self._setRect()
		self._clusterNotes()

	def draw(self,canvas,scale):
		for note in self._children:
			note.draw(canvas,scale)
		x = self._xPos
		t = self._rect.top
		b = self._rect.bottom
		pygame.draw.line(canvas,pygame.Color("black"),(x,t),(x,b),2)

	def dist(self,point):
		"""
		  The distance function here will return the distance, in page
		  coordinates, to the closest part of the stem.
		"""
		return self._distVertLine()

	def _setRect(self):
		x = self._xPos
		yTop = self._parent._yMiddle + int((STAFFSPACING/2.0)*self._baseLine)
		yBot = yTop
		if self._direction == 1:
			yTop -= self._length*STAFFSPACING/2.0
		else:
			yBot += self._length*STAFFSPACING/2.0
		self._rect = pygame.Rect(x-1,yTop,2,yBot-yTop)

	def _reorg(self):
		self._orderNotes()

		# the base note is the lowest on the page (highest y)
		if self._direction == 1:
			maxPos = self._children[-1]._line
			self._length -= self._baseLine-maxPos
			self._baseLine = maxPos
		# the base note is the highest on the page (lowest y)
		else:
			minPos = self._children[0]._line
			self._length -= minPos-self._baseLine
			self._baseLine = minPos

		# prevent the stem from becoming super-short
		self._length = max(self._length,MINSTEMLENGTH)
		self._setRect()
		self._clusterNotes()

	def addNotes(self,children):
		for note in children:
			self._children.append(note)
			note.staffToStem(self)

		self._orderNotes()
		self._clusterNotes()

	# TODO: move to bottom and top line rather than base and length?

	def _orderNotes(self):
		"""
		  Whenever the stem references self._children, it assumes that it is
		  in order, from lowest to highest line.  This function ensures that
		  that is the case.
		"""
		# Build "Order" to contain the sorted order of references into noteDict
		noteDict = {}
		for note in self._children:
			noteDict[note._line] = note
		order = noteDict.keys()
		order.sort()

		# Rebuild the list with the correct note ordering
		self._children = [noteDict[index] for index in order]

	def _clusterNotes(self):
		"""
			This function computes the correct x-position (left or right of the
			stem) for each note in a chord, taking into account the effect of
			"clustered" notes (ones a second apart)
		"""
		# For a down-stem:
		if self._direction == -1:
			self._children[0].setSide(-self._direction)
			for i in range(1,len(self._children)):
				if (self._children[i-1]._line == self._children[i]._line-1):
					self._children[i].setSide(-self._children[i-1]._xPos)
				else:
					self._children[i].setSide(-self._direction)
		# For an up-stem:
		else:
			self._children[-1].setSide(-self._direction)
			for i in range(1,len(self._children)):
				if (self._children[-i]._line == self._children[-i-1]._line+1):
					self._children[-i-1].setSide(-self._children[-i]._xPos)
				else:
					self._children[-i-1].setSide(-self._direction)

	def isStemUp(self):
		return self._direction

	def _cantSurviveWithoutChildren(self):
		return True

def getClosestStaff(staves,point):
	dist = inf
	best = None
	for staff in staves:
		if staff.dist(point) < dist:
			dist = staff.dist(point)
			best = staff
	return best, dist
