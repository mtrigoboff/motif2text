'''
Prints out the contents of a Motif file.

Based on the excellent work done by Chris Webb, who did a lot of helpful
reverse engineering on the Motif file format, and wrote Python code
based on that. I used his work as a starting point for this code.
Link: http://www.motifator.com/index.php/forum/viewthread/460307/

@author:  Michael Trigoboff
@contact: mtrigoboff@comcast.net
@contact: http://spot.pcc.edu/~mtrigobo

Copyright 2012, 2013 Michael Trigoboff.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program as file gpl.txt.
If not, see <http://www.gnu.org/licenses/>.
'''

import collections, os.path, struct, sys

SONG_ABBREV =		'Sg'
PATTERN_ABBREV =	'Pt'

FILE_HDR_LGTH =					 64
CATALOG_ENTRY_LGTH =			  8
BLOCK_HDR_LGTH =				 12
ENTRY_HDR_LGTH =				  8
ENTRY_FIXED_SIZE_DATA_LGTH =	 22
DMST_DATA_SIZE =				560

FILE_HDR_ID =		b'YAMAHA-YSFC'
BLOCK_ENTRY_ID =	b'Entr'
BLOCK_DATA_ID =		b'Data'

BANKS = ('PRE1', 'PRE2', 'PRE3', 'PRE4', 'PRE5', 'PRE6', 'PRE7', 'PRE8',
		 'USR1', 'USR2', 'USR3', 'USR4', 'GM',   'GMDR', 'PDR',  'UDR')

# globals
catalog =				{}
waveforms =				[]
waveformDuplicates =	{}

voiceBlockRead = 		False
voices =				[]
mixingVoices =			[]
sampleVoices =			[]

def bankSectionNumberStr(bank, item):
	number =			item & 0x7f
	section =			number >> 4
	itemInSection =		number & 0x0f
	return '%s:%03d(%c%02d)' % (BANKS[bank], number + 1, ord('A') + section, itemInSection + 1)

# enum corresponds to how these types are defined in the Motif file
class MasterTargetType:
	MST_VOICE, MST_PERFORMANCE, MST_PATTERN, MST_SONG = range(4)

def printMaster(entryNumber, entryName, data):
	dataId, targetType, targetBank, target = struct.unpack('> 4s 32x B x B B 520x', data)
	assert dataId == BLOCK_DATA_ID, BLOCK_DATA_ID
	targetBank &= 0x0F		# guess about keeping bank in range
	print('%03d: %-20s ' % (entryNumber + 1, entryName), end='')
	if targetType == MasterTargetType.MST_VOICE:
		print('Vc', bankSectionNumberStr(targetBank, target))
	elif targetType == MasterTargetType.MST_PERFORMANCE:
		print('Pf', bankSectionNumberStr(targetBank + 8, target))
			# targetBank + 8 because Performances start in bank USR1
	else:
		if targetType == MasterTargetType.MST_PATTERN:	
			print(PATTERN_ABBREV, end='')
		else:
			assert targetType == MasterTargetType.MST_SONG
			print(SONG_ABBREV, end='')
		print(' %02d' % (target + 1))

def printPerformance(entryNumber, entryName, data):
	print(bankSectionNumberStr(((entryNumber & 0x0780) >> 7) + 8, entryNumber & 0x007F),
		  entryName.split(':')[-1])

def doVoice(entryNumber, entryName, data):
	bankNumber = (entryNumber & 0x00FF00) >> 8
	voiceNumber = entryNumber & 0x0000FF
	voiceName = entryName.split(':')[-1]
	if bankNumber < 16:
		voices.append([bankNumber, voiceNumber, voiceName])
	elif bankNumber == 40:
		voices.append([15, voiceNumber, voiceName])
	elif bankNumber == 134:
		sampleVoices.append([entryNumber, bankNumber, voiceNumber, voiceName])
	else:	# Mixing Voice
		mixingVoices.append([entryNumber, bankNumber, voiceNumber, voiceName])

def printVoice(bankNumber, voiceNumber, voiceName):
	print(bankSectionNumberStr(bankNumber, voiceNumber), voiceName)

def printVoices(name):
	print('%s (%d)' % (name, len(voices)))
	for voice in voices:
		printVoice(voice[0], voice[1], voice[2])
	print()

def printSpecialVoices(voices):
	for voice in voices:
		_, bankNumber, voiceNumber, voiceName = voice
		if bankNumber > 192:			# guess at where it switches to pattern
			songPatternStr = PATTERN_ABBREV
		else:
			songPatternStr = SONG_ABBREV
		print('%s %02d:%03d %s' % (songPatternStr, bankNumber - 127, voiceNumber - 127, voiceName))
	print()

def printMixingVoices(name):
	mixingVoices.sort(key = lambda mixVoice: mixVoice[0])
	print('%s (%d)' % (name, len(mixingVoices)))
	printSpecialVoices(mixingVoices)

def printSampleVoices(name):
	print('%s (%d)' % (name, len(sampleVoices)))
	printSpecialVoices(sampleVoices)

def doWaveform(entryNumber, entryName, data):					# entryNumber range is [0 .. 2047]
	waveformNumber = entryNumber - 128
	waveformName = entryName.split(':')[-1]
	waveforms.append([waveformNumber, waveformName])
	if waveformName in waveformDuplicates:
		waveformDuplicates[waveformName].append(waveformNumber)
	else:
		waveformDuplicates[waveformName] = [waveformNumber]

def printWaveforms(name):
	print('%s (%d)' % (name, len(waveforms)))
	for waveform in waveforms:
		waveformNumber, waveformName = waveform
		waveformNumbers = waveformDuplicates[waveformName]
		print('%04d:' % (waveformNumber), waveformName)			# waveformNumber range is [1 .. 2048]
		if len(waveformNumbers) > 1:
			print('  duplicates: ', end='')
			print([wfn for wfn in waveformNumbers if wfn != waveformNumber])
	print()

def printUserArpeggio(entryNumber, entryName, data):
	print('%03d:' % (entryNumber + 1), entryName.split(':')[-1])

def printDefault(entryNumber, entryName, data):
	print('%02d:' % (entryNumber + 1), entryName)

class BlockSpec:
	def __init__(self, ident, name, doFn, printFn, needsData):
		self.ident =			ident
		self.name =				name
		self.doFn =				doFn			# what to do with each item of this type
		self.printFn =			printFn			# print items of this type if not done by doFn
		self.needsData =		needsData

# when printing out all blocks, they will print out in this order
blockSpecs = collections.OrderedDict((
	('sg',  BlockSpec(b'ESNG',	'Songs',			printDefault,		None,				False)),		\
	('pt',  BlockSpec(b'EPTN',	'Patterns',			printDefault,		None,				False)),		\
	('ms',  BlockSpec(b'EMST',	'Masters',			printMaster,		None,				True)),			\
	('mv',  BlockSpec(b'EVCE',	'Mixing Voices',	doVoice,			printMixingVoices,	False)),		\
	('sv',  BlockSpec(b'EVCE',	'Sample Voices',	doVoice,			printSampleVoices,	False)),		\
	('pf',  BlockSpec(b'EPFM',	'Performances',		printPerformance,	None,				False)),		\
	('vc',  BlockSpec(b'EVCE',	'Voices',			doVoice,			printVoices,		False)),		\
	('ua',  BlockSpec(b'EARP',	'User Arpeggios',	printUserArpeggio,	None,				False)),		\
	('wf',  BlockSpec(b'EWFM',	'Waveforms',		doWaveform,			printWaveforms,		False)),		\
	('sm',  BlockSpec(b'ESMT',	'Song Mixings',		printDefault,		None,				False)),		\
	('pm',  BlockSpec(b'EPMT',	'Pattern Mixings',	printDefault,		None,				False)),		\
	('pc',  BlockSpec(b'EPCH',	'Pattern Chains',	printDefault,		None,				False)),		\
	#				   EWIM seems to be a duplicate of EWFM
	# voice data of the 3 different kinds is collected from the EVCE block
	))

def doBlock(blockSpec):
	global catalog, voiceBlockRead
	
	try:
		inputStream.seek(catalog[blockSpec.ident])
	except:
		print('no data of type: %s(%s)\n' % (blockSpec.name, blockSpec.ident.decode('ascii')))
		return

	blockHdr = inputStream.read(BLOCK_HDR_LGTH)
	blockIdData, nEntries = struct.unpack('> 4s 4x I', blockHdr)

	assert blockIdData == blockSpec.ident, blockSpec.ident
	
	if blockSpec.printFn == None:
		print(blockSpec.name)

	if blockSpec.ident != b'EVCE' or not voiceBlockRead:
		for _ in range(0, nEntries):
			entryHdr = inputStream.read(ENTRY_HDR_LGTH + ENTRY_FIXED_SIZE_DATA_LGTH)
			entryId, entryLgth, dataSize, dataOffset, entryNumber = \
				struct.unpack('> 4s I 4x I 4x I I 2x', entryHdr)
			assert entryId == BLOCK_ENTRY_ID, BLOCK_ENTRY_ID
			entryStrs = inputStream.read(entryLgth - ENTRY_FIXED_SIZE_DATA_LGTH)
			entryStrs = entryStrs.decode('ascii')
			entryName = entryStrs.rstrip('\x00').split('\x00')[0]
			if blockSpec.needsData:
				entryPosn = inputStream.tell()
				dataIdent = bytearray(blockSpec.ident)
				dataIdent[0] = ord('D')
				dataIdent = bytes(dataIdent)
				inputStream.seek(catalog[dataIdent] + dataOffset)
				blockData = inputStream.read(dataSize + 8)
				inputStream.seek(entryPosn)
			else:
				blockData = None
			blockSpec.doFn(entryNumber, entryName, blockData)
		if blockSpec.ident == b'EVCE':	# only need to read 'EVCE' block once
			voiceBlockRead = True

	if blockSpec.printFn == None:
		print()
		
	if blockSpec.printFn != None:
		blockSpec.printFn(blockSpec.name)

def processFile(fileName, selectedItems):
	global inputStream
	
	# open file
	try:
		inputStream = open(fileName, 'rb')
	except IOError:
		print('could not open file: %s' % fileName)
		return

	# read file header
	fileHdr = inputStream.read(FILE_HDR_LGTH)
	fileHdrId, fileVersion, catalogSize = struct.unpack('> 16s 16s I 28x', fileHdr)
	assert fileHdrId[0:len(FILE_HDR_ID)] == FILE_HDR_ID, FILE_HDR_ID
	fileVersion = fileVersion.decode('ascii').rstrip('\x00')
	
	# build catalog
	for _ in range(0, int(catalogSize / CATALOG_ENTRY_LGTH)):
		entry = inputStream.read(CATALOG_ENTRY_LGTH)
		entryId, offset = struct.unpack('> 4s I', entry)
		catalog[entryId] = offset

	print(os.path.basename(fileName), '\n')
	if len(selectedItems) == 0:					# print everything
		for blockSpec in blockSpecs.values():
			doBlock(blockSpec)
	else:										# print selectedItems
		# cmd line specifies what to print
		for blockAbbrev in selectedItems:
			try:
				doBlock(blockSpecs[blockAbbrev])
			except KeyError:
				print('unknown data type: %s\n' % blockAbbrev)
	
	inputStream.close()
