#!/usr/bin/env python
# encoding: utf-8
"""
readEig.py

Usage: python readEig.py eig.txt

reads in a VariFlex file into a dictionary of numpy arrays.

VariFlex uses eigenvalue decomposition to calculate k(T,P).  The magnitude of the eigenvalue in the first array tells us whether it corresponds to chemical reaction or internal relaxation of energy.  The second array is k(T,P) for each of the wells, which each column corresponding to a well, and each row corresponding to an eigenvalue.  The third array is the k(T,P) for the product channels.  The beauty of this system is that, provided the eigenvalue is accurately determined, we have a closed-form solution for k(T,P).

Created by Richard West on 2009-06-09.
Copyright (c) 2009 MIT. All rights reserved.
"""

import sys
import os
import fileinput
import re
import numpy

	
def getArray(f, fieldWidth=11):
	"""(array,line) = getArray(f, fieldWidth=11) 
	   reads in an array of floating point values 
	   in fixed-width (fieldWidth) columns on multiple rows
	   from the file-like object f (we expect 'for line in f:' to work)
	   returns (array,line) where array is a numpy array and 
	   line is the next line of f after the array"""
	listOfLists=list()
	numColumns=0
	for line in f:
		try:
			myList = [float(i) for i in re.findall('(.{%d})'%fieldWidth,line)] #line[1:]
		except ValueError: 
			#print "couldn't get array values from ",line
			break
		if numColumns:
			if numColumns!=len(myList): break
		else:
			numColumns=len(myList)
		listOfLists.append(myList)
	array=numpy.array(listOfLists)
	# we've read one line too many, but can't rewind f, so return it to the caller
	return (array,line)

if __name__ == '__main__':
	f=fileinput.input()
	data=dict()
	for line in f:
		match=re.search('Projected Eigenvectors for T =\s+(?P<temperature>\S+)\s+K',line)
		if match: # we found a temperature
			temperature=float(match.group('temperature'))
			if not data.has_key(temperature): # if it's not already in data...
				data[temperature]=dict()      # ...then add it
				continue # read the next line
		match=re.search('and Pressure =\s+(?P<pressure>\S+)\s+Torr',line)
		if match: # we found a pressure
			pressure=float(match.group('pressure'))
			if not data[temperature].has_key(pressure):
				data[temperature][pressure]=dict()
			continue # read the next line
		if re.search('Starting in fragments',line):
			(a,line)=getArray(f)
			a.shape # dimensions of a
			data[temperature][pressure]['populations']=a[:,:-2]
			data[temperature][pressure]['eigenvalues']=a[:,-2] # second-last column of a
			data[temperature][pressure]['normalised_eigenvalues']=a[:,-1] # last column of a
			
			assert re.search('phenomenological rate coefficients for the wells',line)#check next line is what we expect
			line=f.next() # advance a line
			assert re.search('total products and total rate constant at each stage in the sum',line) # check it's what we expect
			(k,line)=getArray(f)
			data[temperature][pressure]['well_rate_constants']=k
			assert re.search('phenomenological rate coefficients for  each product at each stage in the sum',line) # check it's what we expect
			(k2,line)=getArray(f)
			data[temperature][pressure]['product_rate_constants']=k2
				
	fileinput.close()