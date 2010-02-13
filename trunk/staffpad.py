import pygame
from numpy import *
import MusicObjects
import Symbols
pygame.init()

# Global vars: --------------------------------------
# Default window size:
width = 512
height = 512

def makeBackground(width, height):
	"""
	Make our backround surface
	"""
	background = pygame.surface.Surface((width, height))
	background.fill(pygame.Color("white"))
	background = background.convert()
	return background

def main():
	"""
	Simple Pygame to show off tablet pressure sensitivity.
	"""
	# Pull in globals, since they can be modified due to screen resize
	global width
	global height

	radius = 1
	zoom = 1
	objects = []

	screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
	pygame.display.set_caption("StaffPad v0.0");
	background = makeBackground(width, height)
	for i in range(4):
		s = MusicObjects.Staff((0,100*i+110),width)
		objects.append(s)
		s.draw(background,zoom);
#		for j in range(5):
#			h = 15*j+100*i+60
#			pygame.draw.line(background, pygame.Color("black"), (0,h), (width,h), linewidth)
	screen.blit(background, (0,0))

	overlay = pygame.surface.Surface(screen.get_size(), flags=pygame.SRCALPHA, depth=32)
	overlay.convert_alpha()
	overlay.fill((0,0,0,0))

	mouseSurf = pygame.surface.Surface((radius*2,radius*2),flags=pygame.SRCALPHA, depth=32)
	mouseSurf.convert_alpha()
	mouseSurf.fill((0,0,0,0))


	xPos, yPos = pygame.mouse.get_pos()
	xPrev = xPos
	yPrev = yPos

	drawing = 0;
	shape = [];

	# Main loop:
	looping = True
	while looping:
		events = pygame.event.get()
		for event in events:
			if event.type == pygame.QUIT:
				# allow for exit:
				looping = False
			# If the window is resized, update the Pygame screen, and update
			# the area of our tablet:
			if event.type == pygame.VIDEORESIZE:
				width, height = event.size
				screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
				# Copy our old background, to apply that image to the new one:
				oldBg = background.copy()
				background = makeBackground(width, height)
				background.blit(oldBg, (0,0))
				oldOv = overlay.copy()
				overlay = makeBackground(width, height)
				background.blit(oldOv, (0,0))

		#overlay.fill((0,0,0,0))

		xPrev = xPos
		yPrev = yPos
		xPos, yPos = pygame.mouse.get_pos()

		# If user is pressing the button 0, or button 3, (LMB, RMB) draw:
		mouseButtons = pygame.mouse.get_pressed()
		if mouseButtons[0]:
			drawing = 1
			#if len(shape) == 0 or abs(shape[-1][0]-xPos) + abs(shape[-1][1]-yPos) > 1:
			if len(shape) == 0 or shape[-1][0] != xPos or shape[-1][1] != yPos:
				shape.append([xPos,yPos])
			#pygame.draw.circle(overlay, pygame.Color("black"), (xPos,yPos), radius)
			pygame.draw.line(overlay, pygame.Color("black"), (xPrev,yPrev), (xPos,yPos), radius*2)
		else:
			# If we just finished, analyze the shape...
			if drawing == 1:
				drawing = 0
				#print "analyzing shape!"
				#print shape
				#shape = array(shape)
				type = Symbols.classify(shape);
				print type
				pos = Symbols.center(shape);
				if type == 'circle' or type == 'dot':
					# correct position according to closest staff
					close_staff = MusicObjects.get_closest(objects,pos,MusicObjects.TYPE_STAFF)
					# make note object
					if type == 'dot':
						n = MusicObjects.Note(pos,MusicObjects.NOTE_FILLED,close_staff)
					elif type == 'circle':
						n = MusicObjects.Note(pos,MusicObjects.NOTE_EMPTY,close_staff)

					# draw note
					objects.append(n)
					n.draw(background,zoom);
				# erase ink
				# pygame.draw.rect(overlay, (0,0,0,0), (0,0), (width,height));
				overlay.fill((0,0,0,0))
				shape = []
		if mouseButtons[1]:
			#pygame.draw.circle(overlay, pygame.Color("white"), (xPos,yPos), radius)
			#pygame.draw.line(overlay, pygame.Color("white"), (xPrev,yPrev), (xPos,yPos), radius*2)
			pygame.draw.line(overlay, (0,0,0,0), (xPrev,yPrev), (xPos,yPos), radius*4)

		# Draw our mouse pointer representation:
		pygame.draw.circle(mouseSurf, pygame.Color("orange"), (radius,radius), radius)

		screen.blit(background, (0,0))
		screen.blit(overlay, (0,0))
		screen.blit(mouseSurf, (xPos-radius,yPos-radius))
		#screen.blit(mouseSurf, (0,0))
		pygame.display.flip()

	pygame.quit()



if __name__ == "__main__":
	main()
