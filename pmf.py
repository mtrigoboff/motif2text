import sys
from processFile import blockSpecs, processFile

help1Str = \
'''
To print everything in a Motif file, type:

   python pmf.py motifFileName

If you want to save the output into a file, do this:

   python pmf.py ... > outputFileName

To print selected data types in a Motif file, specify those
data types before the file name. The example below will print
all Songs and all Patterns:

   python pmf.py sg pt motifFileName

The two-letter abbreviations for the various data types are:
'''

help2Str = \
'''
Copyright 2012-2014 Michael Trigoboff.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.'''

VERSION = '3.0'

if len(sys.argv) == 1:
	# print help information
	print('pmf (Print Motif File)')
	print('version %s' % VERSION)
	print('by Michael Trigoboff\nmtrigoboff@comcast.net\nhttp://spot.pcc.edu/~mtrigobo')
	print(help1Str)
	for blockFlag, blockSpec in blockSpecs.items():
		print('   %s    %s' % (blockFlag, blockSpec.name.lower()))
	print(help2Str)

# process file
elif len(sys.argv) > 2:
	arg2 = sys.argv[2:]
else:
	arg2 = ()
try:
	processFile(sys.argv[1], arg2)
except Exception as e:
	print('file problem (%s)' % e, file=sys.stderr)
