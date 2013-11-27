'''
Prints out (some of) the contents of a Motif file. The choice of which items
to print reflects the interests of the code's author.

Written to be extensible, so that other items can be printed if desired.

Based on the excellent work done by Chris Webb, who did a lot of helpful
reverse engineering on the Motif file format, and wrote Python code
based on that. I used his work as a starting point for this code.
Link: http://www.motifator.com/index.php/forum/viewthread/460307/

@author:  Michael Trigoboff
@contact: mtrigoboff@comcast.net
@contact: http://spot.pcc.edu/~mtrigobo
'''

import os.path, struct, sys

VERSION = '1.5'

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
mixVoices =				[]
sampleVoices =				[]
waveforms =				[]
waveformDuplicates =	{}

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
		printVoice(bankNumber, voiceNumber, voiceName)
	elif bankNumber == 40:
		printVoice(15, voiceNumber, voiceName)
	elif bankNumber == 134:
		sampleVoices.append([entryNumber, bankNumber, voiceNumber, voiceName])
	else:	# Mix Voice
		mixVoices.append([entryNumber, bankNumber, voiceNumber, voiceName])

def printVoice(bankNumber, voiceNumber, voiceName):
	if bankNumber < 16:
		print(bankSectionNumberStr(bankNumber, voiceNumber), voiceName)
	elif bankNumber == 40:
		print(bankSectionNumberStr(15, voiceNumber), voiceName)

def printSpecialVoices(voices):
	for voice in voices:
		_, bankNumber, voiceNumber, voiceName = voice
		if bankNumber > 192:			# guess at where it switches to pattern
			songPatternStr = PATTERN_ABBREV
		else:
			songPatternStr = SONG_ABBREV
		print('%s %02d:%03d %s' % (songPatternStr, bankNumber - 127, voiceNumber - 127, voiceName))
	print()

def printMixVoices():
	mixVoices.sort(key = lambda mixVoice: mixVoice[0])
	print('Mix Voices (%d)' % len(mixVoices))
	printSpecialVoices(mixVoices)

def printSampleVoices():
	print('Sample Voices (%d)' % len(sampleVoices))
	printSpecialVoices(sampleVoices)

def doWaveform(entryNumber, entryName, data):			# entryNumber range is [0 .. 2047]
	waveformNumber = entryNumber - 128
	waveformName = entryName.split(':')[-1]
	waveforms.append([waveformNumber, waveformName])
	if waveformName in waveformDuplicates:
		waveformDuplicates[waveformName].append(waveformNumber)
	else:
		waveformDuplicates[waveformName] = [waveformNumber]

def printWaveforms():
	print('Waveforms (%d)' % len(waveforms))
	for waveform in waveforms:
		waveformNumber, waveformName = waveform
		waveformNumbers = waveformDuplicates[waveformName]
		print('%04d:' % (waveformNumber), waveformName)			# waveformNumber range is [1 .. 2048]
		if len(waveformNumbers) > 1:
			print('  duplicates: ', end='')
			print([wfn for wfn in waveformNumbers if wfn != waveformNumber])
	print()

def printDefault(entryNumber, entryName, data):
	print('%02d:' % (entryNumber + 1), entryName)

class BlockType:
	def __init__(self, ident, title, doFn, needsData, delayedPrint):
		self.ident =		ident
		self.title =		title
		self.doFn =			doFn			# what to do with each item of this type
		self.needsData =	needsData
		self.delayedPrint =	delayedPrint

blockTypes = (BlockType(b'ESNG',	'Songs',			printDefault,		False,		False),			\
			  BlockType(b'ESMT',	'Song Mixings',		printDefault,		False,		False),			\
			  BlockType(b'EPTN',	'Patterns',			printDefault,		False,		False),			\
			  BlockType(b'EPMT',	'Pattern Mixings',	printDefault,		False,		False),			\
			  BlockType(b'EPCH',	'Pattern Chains',	printDefault,		False,		False),			\
			  BlockType(b'EMST',	'Masters',			printMaster,		True,		False),			\
			  BlockType(b'EPFM',	'Performances',		printPerformance,	False,		False),			\
			  BlockType(b'EVCE',	'Voices',			doVoice,			False,		False),			\
			  BlockType(b'EARP',	'Arpeggios',		printDefault,		False,		False),			\
			  BlockType(b'EWFM',	'Waveforms',		doWaveform,			False,		True),			\
#			  EWIM seems to be a duplicate of EWFM
#			  BlockType(b'EWIM',	'Waveforms2',		printDefault,		False),			\
			  )

def printBlock(blockType):
	global catalog

	try:
		inputStream.seek(catalog[blockType.ident])
	except:
		print('no data of type: %s(%s)\n' % (blockType.title, blockType.ident.decode('ascii')))
		return
	
	blockHdr = inputStream.read(BLOCK_HDR_LGTH)
	blockIdData, nEntries = struct.unpack('> 4s 4x I', blockHdr)
	assert blockIdData == blockType.ident, blockType.ident
	if not blockType.delayedPrint:
		print(blockType.title)
	for _ in range(0, nEntries):
		entryHdr = inputStream.read(ENTRY_HDR_LGTH + ENTRY_FIXED_SIZE_DATA_LGTH)
		entryId, entryLgth, dataSize, dataOffset, entryNumber = \
			struct.unpack('> 4s I 4x I 4x I I 2x', entryHdr)
		assert entryId == BLOCK_ENTRY_ID, BLOCK_ENTRY_ID
		entryStrs = inputStream.read(entryLgth - ENTRY_FIXED_SIZE_DATA_LGTH)
		entryStrs = entryStrs.decode('ascii')
		entryName = entryStrs.rstrip('\x00').split('\x00')[0]
		if blockType.needsData:
			entryPosn = inputStream.tell()
			dataIdent = bytearray(blockType.ident)
			dataIdent[0] = ord('D')
			dataIdent = bytes(dataIdent)
			inputStream.seek(catalog[dataIdent] + dataOffset)
			blockData = inputStream.read(dataSize + 8)
			inputStream.seek(entryPosn)
		else:
			blockData = None
		blockType.doFn(entryNumber, entryName, blockData)	
	if not blockType.delayedPrint:
		print()

def printMotifFile(inputStream):
	# file header
	fileHdr = inputStream.read(FILE_HDR_LGTH)
	fileHdrId, fileVersion, catalogSize = struct.unpack('> 16s 16s I 28x', fileHdr)
	assert fileHdrId[0:len(FILE_HDR_ID)] == FILE_HDR_ID, FILE_HDR_ID
	fileVersion = fileVersion.decode('ascii').rstrip('\x00')
	
	# build catalog
	nCatalogEntries = int(catalogSize / CATALOG_ENTRY_LGTH)
	for _ in range(0, nCatalogEntries):
		entry = inputStream.read(CATALOG_ENTRY_LGTH)
		entryId, offset = struct.unpack('> 4s I', entry)
		catalog[entryId] = offset

	for blockType in blockTypes:
		printBlock(blockType)
	
	if len(mixVoices) > 0:
		printMixVoices()

	if len(sampleVoices) > 0:
		printSampleVoices()

	if len(waveforms) > 0:
		printWaveforms()

# when invoked from the command line
if __name__ == '__main__':
	if len(sys.argv) == 2:
		fileName = sys.argv[1]
		print(os.path.basename(fileName), '\n')
		inputStream = open(fileName, 'rb')
		printMotifFile(inputStream)
		inputStream.close()
	else:
		print('pmf version %s\nneed 1 command line arg: motif file name' % (VERSION))
