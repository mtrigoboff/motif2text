import os, struct, sys

FILE_HDR_LGTH =			 64
CATALOG_ENTRY_LGTH =	  8
BLOCK_HDR_LGTH =		 12
ENTRY_HDR_LGTH =		 30
DMST_DATA_SIZE =		560

FILE_HDR_ID =			b'YAMAHA-YSFC'
BLOCK_ENTRY_ID =		b'Entr'
BLOCK_DATA_ID =			b'Data'

SECTION_LETTERS =		'ABCDEFGH'

catalog = {}

def printDefault(entryNumber, entryName, data):
	print('%02d:' % (entryNumber + 1), entryName)

class MasterTargetType:
	MST_VOICE, MST_PERFORMANCE, MST_PATTERN, MST_SONG = range(4)

def printMaster(entryNumber, entryName, data):
	targetType, target = struct.unpack('> 36x b 2x b 520x', data)
	targetName = \
		{MasterTargetType.MST_VOICE			: 'Voice',
		 MasterTargetType.MST_PERFORMANCE	: 'Performance',
		 MasterTargetType.MST_PATTERN		: 'Pattern',
		 MasterTargetType.MST_SONG			: 'Song'} \
	  [targetType]
	print('%03d:' % (entryNumber + 1), entryName, '(%s %d)' % (targetName, target))

def printPerformance(performanceNumber, entryName, data):
	userBank =			int(performanceNumber / 128)
	numberInSection =	performanceNumber % 128
	section =			int(numberInSection / 16)
	keyNumber =			int(performanceNumber % 16)
	print('USR%d:%03d(%c%02d) %s' %
		  (userBank + 1, numberInSection + 1, SECTION_LETTERS[section], keyNumber + 1,
		   entryName.split(':')[-1]))

class BlockType:
	def __init__(self, ident, title, printFn, needsData):
		self.ident = ident
		self.title = title
		self.printFn = printFn
		self.needsData = needsData

blockTypes = (BlockType(b'ESNG',	'Songs',		printDefault,		False),			\
			  BlockType(b'EPTN',	'Patterns',		printDefault,		False),			\
			  BlockType(b'EMST',	'Masters',		printMaster,		True),			\
			  BlockType(b'EPFM',	'Performances',	printPerformance,	False)			\
			  )

def printBlock(blockType):
	inputStream.seek(catalog[blockType.ident])
	blockHdr = inputStream.read(BLOCK_HDR_LGTH)
	blockIdData, nEntries = struct.unpack('> 4s 4x I', blockHdr)
	assert blockIdData == blockType.ident, blockType.ident
	print(blockType.title)
	for _ in range(0, nEntries):
		entryHdr = inputStream.read(ENTRY_HDR_LGTH)
		entryId, entryLgth, dataSize, dataOffset, entryNumber = \
			struct.unpack('> 4s I 4x I 4x I I 2x', entryHdr)
		assert entryId == BLOCK_ENTRY_ID, BLOCK_ENTRY_ID
		entryStrs = inputStream.read(entryLgth - ENTRY_HDR_LGTH + 8)
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
		blockType.printFn(entryNumber, entryName, blockData)	
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

# when invoked from the command line
if __name__ == '__main__':
#	print(sys.executable)
	if len(sys.argv) == 2:
#		try:
		fileName = sys.argv[1]
# 		print('working directory: ', os.getcwd(), sep='')
		print('file:              ', fileName, '\n', sep='')
		inputStream = open(fileName, 'rb')
		printMotifFile(inputStream)
#		except Exception as e:
#			errorMsg = '--> ' + str(e.args[0])
#			print(errorMsg)
#			print(errorMsg, file=sys.stderr)
		inputStream.close()

	else:
		print('no args')
