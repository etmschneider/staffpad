import pygame
from numpy import *
from time import time
import MusicObjects as mus
import Symbols

# TODO: put this in a config/parameters file that can easily be changed.
CLASSIFYTIMETHRESHOLD = 0.2

def makeBackground(size):
	"""
	  Non-transparent surface where the content is displayed
	"""
	background = pygame.surface.Surface(size)
	background.fill(pygame.Color("white"))
	background = background.convert()
	return background

def makeOverlay(size):
	"""
	  Transparent overlay surface where ink can be temporarily stored
	"""
	overlay = pygame.surface.Surface(size, flags=pygame.SRCALPHA, depth=32)
	overlay.convert_alpha()
	overlay.fill((0,0,0,0))
	return overlay

class Page:
	def __init__(self,pad):
		"""
		  This is a "page" of staff paper.  It has staves, which can contain
		  notes and other symbols.
		
		  It shares common attributes, such as page size, with all the other
		  pages in the pad.
		"""
		self.pad = pad

		# A list of the staves on the page
		# TODO: Eventually, these will probably become systems instead
		self.staves = []

		# Initialize the page with four staves
		for i in range(4):
			s = mus.Staff((0,100*i+110),self.pad.pageSize[0])
			self.staves.append(s)

	def removeObjectAtPoint(self,point):
		"""
		  This function removes any object that is underneath the given point.
		"""
		for staff in self.staves:
			# redraw if objects are removed
			if staff.removeAt(point):
				self.pad.redraw()

	def addObject(self,type,rect):
		"""
		  This function attempts to contain all of the logic for determining
		  what a given shape (line, circle, etc) actually means musically.
		  This is probably too much for one function, and should eventually be
		  broken up into smaller chunks in some intelligent way.
		"""
		# Conditions to become a note:
		# - shape must be a circle or a dot
		# - TODO: size must be in the expected range for a note
		if type == 'circle' or type == 'dot':
			center = (0.5*(rect[0][0]+rect[1][0]),0.5*(rect[0][1]+rect[1][1]))

			# get closest staff to attach note to
			staff, dist = mus.getClosest(self.staves,center)

			# make note object
			if type == 'dot':
				n = mus.Note(center,staff,mus.NOTE_FILLED)
			elif type == 'circle':
				n = mus.Note(center,staff,mus.NOTE_EMPTY)

			# attach note to staff, and draw it
			staff.addNote(n)

			# If there is a stem close, attach note to it
			# TODO: do this before staff logic (modify MusicObject stem code
			# to allow this)
			stem, dist = mus.getClosest(staff.objects,center,mus.TYPE_STEM)
			if dist < mus.STAFFSPACING*0.75:
				stem.addNotes((n,))

			# Redraw (necessary because note may affect other clustered notes)
			self.pad.redraw()

		elif type == 'vline':
			center = [0.5*(rect[0][0]+rect[1][0]),0.5*(rect[0][1]+rect[1][1])]
			top = rect[0][1]
			bottom = rect[1][1]
			right = rect[1][0]
			left = rect[0][0]

			# Find the closest staff
			staff, dist = mus.getClosest(self.staves,center)

			# Find the lines which the line starts and ends at
			endlines = [staff.whichLine(top),staff.whichLine(bottom)]

			# Find the closest notes to the top and bottom of the line
			topNote, topDist = mus.getClosest(staff.objects,(right,top),mus.TYPE_NOTE)
			botNote, botDist = mus.getClosest(staff.objects,(left,bottom),mus.TYPE_NOTE)

			# If the vertical line's top or bottom is close to a note,
			# then we make it a stem of that note, giving preference
			# to the closest note (bottom if they are equal)
			if min(botDist,topDist) < mus.STAFFSPACING*0.75:
				stemLen = abs(endlines[0]-endlines[1])
				if botDist <= topDist:
					stem = mus.Stem((center[0],botNote.position[1]),
					                         staff,stemLen,1,[botNote])
				else:
					stem = mus.Stem((center[0],topNote.position[1]),
					                         staff,stemLen,-1,[topNote])

				# Add the object to the staff
				staff.addObject(stem)

				# Find any other notes within range of the stem and attach them
				area = [[center[0]-mus.STAFFSPACING*0.25,center[1]-stemLen],[center[0]+mus.STAFFSPACING*0.25,center[1]+stemLen]]

				chordNotes = mus.getObjectsIn(staff.objects,area,mus.TYPE_NOTE)
				stem.addNotes(chordNotes)

				# Redraw
				self.pad.redraw()

			# Otherwise, for it to be a barline, it must start and end
			# at the staff's top and bottom line
			# TODO: Change these values to a staff constant, based on 
			# staff type
			elif (endlines[0] in [-3,-4,-5] and endlines[1] in [3,4,5]):
				barline = mus.Barline(center[0],staff)
				# draw barline
				staff.addObject(barline)
				barline.draw(self.pad.background,self.pad.zoom);
			else:
				print "unrecognized vertical line"
		else:
			print "unhandled shape"

class StaffPad:
	def __init__(self,width=512,height=512):
		"""
		  Initialize the pad of staff paper.  The pad consists of a collection
		  of pages.  Also, the pad contains the information about what the
		  user is looking at (i.e., which page and area the screen should
		  display).
		"""
		# The current zoom setting.
		self.zoom = 1.0
		# The number of pixels of drawn lines at a unit zoom setting.
		self.radius = 1.0

		# Initialize the screen, background, and overlays
		self.resizeScreen([width,height])
		pygame.display.set_caption("StaffPad v0.2");

		# This is the page size (represents maximum width of staves)
		# TODO: logic of resizing the page.  Bigger is fairly simple, smaller
		# may cause clipping, which should be handled nicely.
		self.pageSize = [width,height]

		# The mouse surface is a small patch where a orange "dot" cursor is 
		# displayed while drawing objects, to feel more like an ink-aware
		# program.  This cursor scales with the zoom.
		self.mouseSurface = makeOverlay((self.zoom*self.radius*2,self.zoom*self.radius*2))

		# Add an initial page
		self.pages = [];
		self.pages.append(Page(self))

		# Set the current page you are looking at.
		self.currentPage = 0

		# Draw the initial staves onto the screen.
		self.redraw()

	def resizeScreen(self,newSize):
		"""
		  Called during initialization or resizing of the screen, and builds the
		  background to display data, and the overlay surface to write ink on.
		"""
		# This is the screen size.  The current screen should be scrollable to
		# view the entire page.  The maximum size should be the current page
		# size times the zoom factor.
		# TODO: add scroll bars.  Until then, the top left corner of the screen
		# will always coincide with the top left corner of the page.
		self.screenSize = newSize

		# The pygame screen on which everything is drawn
		self.screen = pygame.display.set_mode(self.screenSize, pygame.RESIZABLE)

		# The background is the surface where recognized objects are displayed
		self.background = makeBackground(self.screenSize)

		# The overlay is the surface where the "ink" is displayed as objects
		# are drawn
		self.overlay = makeOverlay(self.screenSize)

	def run(self):
		"""
		  This is the main loop which captures and analyzes input, and displays
		  objects on the screen.
		"""

		### Initialize variables that help with capturing gestures.

		# Track the mouse position
		xPos, yPos = pygame.mouse.get_pos()
		xPrev = xPos
		yPrev = yPos

		# drawing describes whether a shape is currently being captured, so that
		# sepecial actions can be taken at the start and end of the gestures
		drawing = 0
		lastDrawTime = inf
		waitToFinish = 0

		# stores the coordinates of points along the drawn path
		shape = [];

		# Main loop for capturing input
		looping = True
		while looping:
			# Catch any major events (quit button pressed, screen resize, etc)
			events = pygame.event.get()
			for event in events:
				# This is caused by pressing the "X" in the top right corner
				if event.type == pygame.QUIT:
					# Causing the while loop to stop, and quits the program.
					# Alternatively, this could be caught with a "do you want
					# to save" message.
					looping = False
				# If the window is resized, update the Pygame screen, the
				# screen area, and cue a redraw
				if event.type == pygame.VIDEORESIZE:
					self.resizeScreen(event.size)
					self.redraw()

			# Update the tracked mouse position
			xPrev = xPos
			yPrev = yPos
			xPos, yPos = pygame.mouse.get_pos()

			# Get mouse buttons (detect whether stylus is touching)
			mouseButtons = pygame.mouse.get_pressed()

			# This means the left mouse button is down, which corresponds to
			# the stylus touching.
			if mouseButtons[0]:
				# Set flag to indicate that a shape is being recorded
				drawing = 1
				# Add a new point, unless the cursor hasn't moved
				if len(shape) == 0 or shape[-1][0] != xPos or shape[-1][1] != yPos:
					shape.append([xPos,yPos])
				# Draw the corresponding line segment on the overlay
				pygame.draw.line(self.overlay, pygame.Color("black"), (xPrev,yPrev), (xPos,yPos), int(self.radius*2))

			# As soon as the button is lifted, go into a waiting state for multi
			# segment gestures to be classified.
			elif drawing == 1:
				# We are no longer drawing; turn off the flag
				drawing = 0
				waitToFinish = 1
				lastDrawTime = time()

			# classify the gesture, and add the object.
			elif waitToFinish and time()-lastDrawTime > CLASSIFYTIMETHRESHOLD:
				waitToFinish = 0
				# classify the gesture into a shape
				type = Symbols.classify(shape)

				# get a bounding rectangle for this shape
				rect = Symbols.boundingBox(shape)

				# Convert screen coordinates to page coordinates!
				pageRect = self.screenToPage(rect)

				# Given the classified shape, we must now determine what it
				# semantically means.  For example, is a vertical line a barline
				# or a note stem?
				# This is done at the page level, which means the coordinates
				# passed in to this function should be page coordinates.
				self.pages[self.currentPage].addObject(type,pageRect)

				# erase the ink from the gesture, and reset the shape
				self.overlay.fill((0,0,0,0))
				shape = []

			# This means the eraser is touching.
			if mouseButtons[1]:
				pagePoint = self.screenToPage([(xPos,yPos)])[0]
				self.pages[self.currentPage].removeObjectAtPoint(pagePoint)

			# Draw our mouse pointer representation:
			pygame.draw.circle(self.mouseSurface, pygame.Color("orange"), (int(self.radius),int(self.radius)), int(self.radius))

			# Blit (write) all of the background and overlay data to the screen 
			self.screen.blit(self.background, (0,0))
			self.screen.blit(self.overlay, (0,0))
			self.screen.blit(self.mouseSurface, (xPos-self.zoom*self.radius,yPos-self.zoom*self.radius))
			pygame.display.flip()
		pygame.quit()

	# This takes a list of points in screen coordinates, and converts to a list
	# in page coordinates.
	def screenToPage(self,pointsIn):
		pointsOut = []
		for p in pointsIn:
			pointsOut.append([p[0]/self.zoom,p[1]/self.zoom])
		return pointsOut

	def redraw(self):
		"""
		  This function redraws the objects on screen after a zoom, scroll,
		  resize, or other change.  It is also responsible for the initial
		  drawing of objects.
		"""
		# TODO: do we have to adjust the background size to be as big as the
		# scaled page size, and then only display part of it on the screen? If
		# this isn't done, will higher zooms or small screens cause objects to
		# be drawn off of the background, causing errors?
		# TODO: can we just do scrolling by adjusting the blit point?

		# First erase, then draw.
		self.background.fill(pygame.Color("white"))
		for staff in self.pages[self.currentPage].staves:
			staff.draw(self.background, self.zoom)
		self.screen.blit(self.background, (0,0))

pygame.init()
pad = StaffPad()
pad.run()
