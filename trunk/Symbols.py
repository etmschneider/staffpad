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

	# Compute the projections of the shape
	xProj = np.sum(shapeBinary,0)
	yProj = np.sum(shapeBinary,1)
	xProjNorm = np.interp(np.linspace(0,1,101),np.linspace(0,1,w),xProj)
	yProjNorm = np.interp(np.linspace(0,1,101),np.linspace(0,1,h),yProj)
	xProjNorm = np.reshape(xProjNorm,[1,101])
	yProjNorm = np.reshape(yProjNorm,[1,101])

	templates = ['dot','circle','flat','sharp','natural','vline','hat'] # vline hat etc...

	# Compute a score for each template
	scores = []
	for name in templates:
		xProjTemplate = np.load('symbols/' + name + '-xproj_mu_sigma.npy');
		yProjTemplate = np.load('symbols/' + name + '-yproj_mu_sigma.npy');
		sizeTemplate = np.load('symbols/' + name + '-size_mu_sigma.npy');

		# Use a sigmoid to approximate the normal CDF for each of these scores
		xProjScore = np.mean(2/(1+np.exp(1.7*np.abs(xProjTemplate[0,:]-xProjNorm)/xProjTemplate[1,:])))
		yProjScore = np.mean(2/(1+np.exp(1.7*np.abs(yProjTemplate[0,:]-yProjNorm)/yProjTemplate[1,:])))
		xSizeScore = 2/(1+np.exp(1.7*np.abs(sizeTemplate[0,1]-w)/np.abs(sizeTemplate[1,1])))
		ySizeScore = 2/(1+np.exp(1.7*np.abs(sizeTemplate[0,0]-h)/np.abs(sizeTemplate[1,0])))

		scores.append(sqrt(sqrt(xProjScore*yProjScore*xSizeScore*ySizeScore)))
		
	mxScore = max(scores)
	if mxScore < 0.2:
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

def train(shape,symbol):
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
	shapeBinary = np.zeros([h,w],int)
	for i in range(np.size(shape,0)):
		shapeBinary[shape[i,1]-mnpts[1],shape[i,0]-mnpts[0]] = 1

	xProj = np.sum(shapeBinary,0)
	yProj = np.sum(shapeBinary,1)
	xProjNorm = np.interp(np.linspace(0,1,101),np.linspace(0,1,w),xProj)
	yProjNorm = np.interp(np.linspace(0,1,101),np.linspace(0,1,h),yProj)
	xProjNorm = np.reshape(xProjNorm,[1,101])
	yProjNorm = np.reshape(yProjNorm,[1,101])

	# Load previous data from file
	name = symbol

	try:
		prev_xProj = np.load('symbols/' + name + '-xproj.npy')
		prev_yProj = np.load('symbols/' + name + '-yproj.npy')
		prev_size = np.load('symbols/' + name + '-size.npy')
	except:
		prev_xProj = np.zeros([0,101])
		prev_yProj = np.zeros([0,101])
		prev_size = np.zeros([0,2])

	xProj = np.concatenate((prev_xProj,xProjNorm),0)
	yProj = np.concatenate((prev_yProj,yProjNorm),0)
	new_size = np.concatenate((prev_size,[[h,w]]),0)

	# These files contain all the past data
	np.save('symbols/' + name + '-xproj',xProj)
	np.save('symbols/' + name + '-yproj',yProj)
	np.save('symbols/' + name + '-size',new_size)

	# These files just contain aggregate data for classification
	np.save('symbols/' + name + '-xproj_mu_sigma',np.concatenate(([np.mean(xProj,0)],[np.std(xProj,0)]),0))
	np.save('symbols/' + name + '-yproj_mu_sigma',np.concatenate(([np.mean(yProj,0)],[np.std(yProj,0)]),0))
	np.save('symbols/' + name + '-size_mu_sigma',np.concatenate(([np.mean(new_size,0)],[np.std(new_size,0)]),0))
