# This file contains templates for various symbols which might be drawn

from numpy import *

circle = array([[ 0.,  0.,  1.,  1.,  0.,  0.],
                [ 0.,  1.,  0.,  0.,  1.,  0.],
                [ 1.,  0.,  0.,  0.,  0.,  1.],
                [ 1.,  0.,  0.,  0.,  0.,  1.],
                [ 0.,  1.,  0.,  0.,  1.,  0.],
                [ 0.,  0.,  1.,  1.,  0.,  0.]])

dot = array([[ 0.,  0.,  1.,  1.,  0.,  0.],
             [ 0.,  1.,  1.,  1.,  1.,  0.],
             [ 1.,  1.,  1.,  1.,  1.,  1.],
             [ 1.,  1.,  1.,  1.,  1.,  1.],
             [ 0.,  1.,  1.,  1.,  1.,  0.],
             [ 0.,  0.,  1.,  1.,  0.,  0.]])

hline = array([[ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]])
hline2 = array([[ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]])

vline = transpose(hline)
vline2 = transpose(hline2)

# These two data structures go together to help return the correct symbol!
templates = [circle,dot,hline,hline2,vline,vline2]
symbols = ['circle','dot','hline','hline','vline','vline']

def center(shape):
	mnpts = amin(shape,0)
	mxpts = amax(shape,0)
	w = mxpts[0] - mnpts[0] + 1
	h = mxpts[1] - mnpts[1] + 1
	return [mnpts[0]+w/2,mnpts[1]+h/2]

def boundingBox(shape):
	mnpts = amin(shape,0)
	mxpts = amax(shape,0)
	return (mnpts,mxpts)
	

# This function contains the logic to classify the shape into a basic symbol -
# a vertical line, empty cirle, filled in circle, sharp or flat, or perhaps
# something more complicated (or none of the above
#
# At the moment, this is done via basic property and template matching.  For
# property matching:
#    Means, standard deviations, and widths/heights are compared to what
#     would be expected (i.e., a vertical line would have a high height/width
#     ratio).
# For template matching:
#    A basic template of each symbol is scaled to the dimensions of the shape,
#     and then each pixel of the shape and template are ANDed, and the ratio of
#     the total number of ones compared to the number in the scaled template
#     become the score for that template.  The highest score (above some
#     threshold) is chosen as the best match.
def classify(shape):
	# Shape is a set of x/y coordinates:
	shape = array(shape)
	mnpts = amin(shape,0)
	mxpts = amax(shape,0)
	w = mxpts[0] - mnpts[0] + 1
	h = mxpts[1] - mnpts[1] + 1

	# Transform into a binary image
	shape_binary = zeros([h,w],int)
	for i in range(size(shape,0)):
		shape_binary[shape[i,1]-mnpts[1],shape[i,0]-mnpts[0]] = 1;

	# debug code!
	#print shape_binary
	#h = size(shape,0)
	#w = size(shape,1)
	scores = []
	for template in templates:
		match = sum(transform(template,w,h) & shape_binary)
		total = sum(transform(template,w,h))
		score1 = double(match)/total
		match = w*h - sum(transform(template,w,h) ^ shape_binary)
		total = w*h
		score2 = double(match)/total
		score3 = (double(w)/h)/(double(size(template,1))/size(template,0))
		score3 = min(score3,1/score3)
		#print "obj1:",score1,score2,score3
		scores.append(score1*score2*score3)
	#print scores
	mx = max(scores)
	return symbols[scores.index(mx)]


# Old property matching code
#	if h/w > 7.0 and h > 10:
#		return "vertline"
#	else:
#		return "unknown"

# Returns the template stretched so it is w pixels wide and h pixels high
def transform(template,w,h):
	res = zeros([h,w],int)
	tw = size(template,1)
	th = size(template,0)
	for i in range(w):
		# float x-position of center of cell
		x = (i+0.5)/w
		for j in range(h):
			# float y-position of center of cell
			y = (j+0.5)/h
			res[j,i] = template[floor(y*th),floor(x*tw)]
	return res
