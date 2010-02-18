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
				elif type == 'vline':
					top = amin(shape,0)[1]
					bottom = amax(shape,0)[1] 
					#TODO: maybe there should be a top and bottom staff?
					close_staff = MusicObjects.get_closest(objects,pos,MusicObjects.TYPE_STAFF)
					topline = close_staff.which_line(top,zoom);
					bottomline = close_staff.which_line(bottom,zoom);

					topNote = MusicObjects.getClosestNoteOnLine(objects,pos[0],close_staff,topline)
					bottomNote = MusicObjects.getClosestNoteOnLine(objects,pos[0],close_staff,bottomline)
					topNoteDist = Inf
					bottomNoteDist = Inf
					if topNote and abs(pos[0]-topNote.position[0]) < MusicObjects.STAFFSPACING*0.75*zoom:
						topNoteDist = abs(pos[0]-topNote.position[0])
					if bottomNote and abs(pos[0]-bottomNote.position[0]) < MusicObjects.STAFFSPACING*0.75*zoom:
						bottomNoteDist = abs(pos[0]-bottomNote.position[0])

					# If the vertical line's top or bottom is close to a note,
					# then we make it a stem of that note, giving preference
					# to the closest note (bottom if they are equal)
					if min(bottomNoteDist,topNoteDist) < Inf:
						if bottomNoteDist <= topNoteDist:
							print "stem for note at bottom of line"
							#TODO: make stem attach to bottom note
						else:
							print "stem for note at top of line"
							#TODO: make stem attach to top note

					# Otherwise, for it to be a barline, it must start and end
					# at the staff's top and bottom line
					# TODO: Change these values to a staff constant, based on 
					# staff type
					elif (topline == -4 and bottomline == 4):
						barline = MusicObjects.Barline(pos[0],close_staff)
						# draw barline
						objects.append(barline)
						barline.draw(background,zoom);
					else:
						print "unrecognized vertical line"
					

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
