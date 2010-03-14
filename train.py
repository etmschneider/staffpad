"""
This file is an interface to training the classifier, as well as easily testing
it.
"""

import pygame
import sys
from numpy import *
from time import time
import MusicObjects
import Symbols

# TODO: put this into config file
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

class Trainer:
	def __init__(self,symbol,symSize):
		width = 120
		height = 120
		"""
		  Initialize the training display.  This display includes a small box
		  in the middle in which you are to draw.
		"""
		# Keep track of what symbol we are training
		self.symbol = symbol
		self.symSize = symSize

		# The pygame screen on which everything is drawn
		self.screen = pygame.display.set_mode([width,height])

		# The background is the surface where permanent objects are displayed
		self.background = makeBackground([width,height])

		# The overlay is the surface where the "ink" is displayed as objects
		# are drawn
		self.overlay = makeOverlay([width,height])

		pygame.display.set_caption("StaffPad Symbol Template Trainer");

		# The mouse surface is a small patch where a orange "dot" cursor is 
		# displayed while drawing objects, to feel more like an ink-aware
		# program.  This cursor scales with the zoom.
		self.mouseSurface = makeOverlay((2,2))

		s = MusicObjects.Staff((0,60),width)

		self.background.fill(pygame.Color("white"))
		s.draw(self.background, 1.0)
		self.screen.blit(self.background, (0,0))

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
		shape = []

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
				pygame.draw.line(self.overlay, pygame.Color("black"), (xPrev,yPrev), (xPos,yPos), int(2))

			# As soon as the button is lifted, go into a waiting state for multi
			# segment gestures to be classified/trained
			elif drawing == 1:
				# We are no longer drawing; turn off the flag
				drawing = 0
				waitToFinish = 1
				lastDrawTime = time()

			# classify/train the shape
			elif waitToFinish and time()-lastDrawTime > CLASSIFYTIMETHRESHOLD:
				waitToFinish = 0

				if self.symbol == 'classify':
					print Symbols.classify(shape)
				else: # Otherwise, train
					Symbols.train(shape,self.symbol,self.symSize)

				# get a bounding rectangle for this shape
				rect = Symbols.boundingBox(shape)

				# erase the ink from the gesture, and reset the shape
				self.overlay.fill((0,0,0,0))
				shape = []

			# Draw our mouse pointer representation:
			pygame.draw.circle(self.mouseSurface, pygame.Color("orange"),(1,1),1)

			# Blit (write) all of the background and overlay data to the screen 
			self.screen.blit(self.background, (0,0))
			self.screen.blit(self.overlay, (0,0))
			self.screen.blit(self.mouseSurface, (xPos-1,yPos-1))
			pygame.display.flip()
		pygame.quit()


if len(sys.argv) != 4 and (len(sys.argv) != 2 or sys.argv[1] != 'classify'):
	print "Usage:"
	print "   python train.py symbol <width> <height>"
	print " or"
	print "   python train.py classify"
	exit()
pygame.init()
if len(sys.argv) == 4:
	train = Trainer(sys.argv[1],(int(sys.argv[2]),int(sys.argv[3])))
else:
	train = Trainer(sys.argv[1],(0,0))
train.run()
