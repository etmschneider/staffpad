# This file is dedicated to the classification of shapes drawn by the user into
# a set of symbols allowed by the program.  The individual symbols are stored in
# the symbols directory, and they have a template file for each size.

import numpy as np
from math import pow, sqrt, pi, exp

def center(shape):
	mnpts = np.amin(shape,0)
	mxpts = np.amax(shape,0)
	w = mxpts[0] - mnpts[0] + 1
	h = mxpts[1] - mnpts[1] + 1
	return [mnpts[0]+w/2,mnpts[1]+h/2]

def boundingBox(shape):
	mnpts = np.amin(shape,0)
	mxpts = np.amax(shape,0)
	return (mnpts,mxpts)
	
def classify(shape):
	"""
	  This function contains the logic to classify the shape into a basic
	  symbol; i.e., a vertical line, empty circle, filled circle, sharp, flat,
	  etc.
	  This is done by first sorting by size and aspect ratio, and then comparing	  the object to a list of approprate symbols templates.  These symbol
	  templates are smaller grids that represent the density of pixels in a
	  larger binary image.

	  After comparing to the existing templates, a score is computed, and the
	  highest score is chosen.
	"""
	# Shape is a set of x/y coordinates:
	shape = np.array(shape)
	mnpts = np.amin(shape,0)
	mxpts = np.amax(shape,0)
	w = mxpts[0] - mnpts[0] + 1
	h = mxpts[1] - mnpts[1] + 1

	# Transform into a binary image
	shapeBinary = np.zeros([h,w],int)
	for i in range(np.size(shape,0)):
		shapeBinary[shape[i,1]-mnpts[1],shape[i,0]-mnpts[0]] = 1;

	# Pick appropriate templates using aspect ratio
	# TODO: could size play a part here, too?
	aspectRatios = [(5,5),(10,1)]
	templates = [['dot','circle','sharp','flat','natural'],['vline']]
	ratioScore = []
	for ratio in aspectRatios:
		wt = ratio[1]
		ht = ratio[0]
		ratioScore.append((w*wt+h*ht)/sqrt(w*w+h*h)/sqrt(wt*wt+ht*ht))
	if max(ratioScore) < 0.85:
		#print "No matching aspect ratio"
		return 'unclassified'

	ratioNum = ratioScore.index(max(ratioScore))
	ratio = aspectRatios[ratioNum]
	templates = templates[ratioNum]
	
	# Transform the shape to the (currently standard) template size
	shapeDensity = densityTransform(shapeBinary,ratio)

	# Compute a score for each template
	scores = []
	for name in templates:
		templateMean = np.load('symbols/' + name + '-' + str(ratio[0]) + 'x' + str(ratio[1]) + '-mean.npy')
		templateStd = np.load('symbols/' + name + '-' + str(ratio[0]) + 'x' + str(ratio[1]) + '-std.npy')
		sc = 0

		# TODO: Do this in a matrix computation instead?
		for i in range(ratio[0]):
			for j in range(ratio[1]):
				# TODO: to be a probability, this should be multiplied, or add
				# the logs to prevent numerical issues...

				# avoid n/0 numerical explosion
				templateStd[i,j] = max(templateStd[i,j],0.001)

				# distance from mean, normalized by standard deviation:
				d = abs(templateMean[i,j]-shapeDensity[i,j])/templateStd[i,j]

				# Use a sigmoid to kinda approximate the normal CDF
				sc += 1-1/(1+np.exp(-(6*d-6)))

		# Normalize over different template sizes
		sc = sc/(ratio[0]*ratio[1])
		scores.append(sc)

	mxScore = max(scores)
	if mxScore < 0.4:
		return 'unclassified'
	else:
		return templates[scores.index(mxScore)]

def densityTransform(input,out_size):
	"""
	  This maps the input binary image into a smaller grid, and assigns each
	  block of this smaller grid a value equal to the proportion it is covered
	  with black squares from the input image.
	"""
	# TODO: This should only work when inputsize is greater that outsize in
	# each dimension.
	w_in = np.size(input,1)
	h_in = np.size(input,0)
	w_out = out_size[1]
	h_out = out_size[0]
	output = np.zeros([h_out+1,w_out+1])

	# Get the left/right and top/bottom input square edges into the output
	# coordinate system.
	x_edges = np.array(range(w_in+1))*np.double(w_out)/w_in
	y_edges = np.array(range(h_in+1))*np.double(h_out)/h_in

	w_tr = np.double(w_out)/w_in
	h_tr = np.double(h_out)/h_in

	dx = np.ceil(x_edges[:-1])-x_edges[:-1]
	dy = np.ceil(y_edges[:-1])-y_edges[:-1]

	# Add the relevant parts of each square to the final output
	for i in range(h_in):
		for j in range(w_in):
			if input[i,j] == 1:
				# Add the four divided area elements
				output[np.floor(y_edges[i]),np.floor(x_edges[j])] += dy[i]*dx[j]
				output[np.floor(y_edges[i+1]),np.floor(x_edges[j])] += (h_tr-dy[i])*dx[j]
				output[np.floor(y_edges[i+1]),np.floor(x_edges[j+1])] += (h_tr-dy[i])*(w_tr-dx[j])
				output[np.floor(y_edges[i]),np.floor(x_edges[j+1])] += dy[i]*(w_tr-dx[j])

	return output[:-1,:-1]

def train(shape,symbol,template_size):
	"""
	  This function takes in a shape from the training program, and averages its
	  density image with the previous stored values for that symbol.
	"""
	# Shape is a set of x/y coordinates:
	shape = np.array(shape)
	mnpts = np.amin(shape,0)
	mxpts = np.amax(shape,0)
	w = mxpts[0] - mnpts[0] + 1
	h = mxpts[1] - mnpts[1] + 1

	# Transform into a binary image
	shape_binary = np.zeros([h,w],int)
	for i in range(np.size(shape,0)):
		shape_binary[shape[i,1]-mnpts[1],shape[i,0]-mnpts[0]] = 1;

	# Transform the large grid of points into densities the size of the
	# template
	new_template = densityTransform(shape_binary,template_size)
	new_template = np.reshape(new_template,(template_size[0],template_size[1],1))

	name = symbol+'-'+str(template_size[0])+'x'+str(template_size[1])

	try:
		prev_template = np.load('symbols/' + name + '.npy')
	except:
		prev_template = np.zeros([template_size[0],template_size[1],0])

	new_template = np.concatenate((prev_template,new_template),2)

	np.save('symbols/'+name,new_template)
	np.save('symbols/'+name+'-mean',np.mean(new_template,2))
	np.save('symbols/'+name+'-std',np.std(new_template,2))
