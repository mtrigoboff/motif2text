import struct, sys

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

catalog = {}

def bankSectionNumberStr(bank, item):
	number =			item & 0x7f
	section =			number >> 4
	itemInSection =		number & 0x0f
	return '%s:%03d(%c%02d)' % (BANKS[bank], number + 1, ord('A') + section, itemInSection + 1)

def printDefault(entryNumber, entryName, data):
	print('%02d:' % (entryNumber + 1), entryName)

class MasterTargetType:
	MST_VOICE, MST_PERFORMANCE, MST_PATTERN, MST_SONG = range(4)
		# enum corresponds to how these types are defined in the Motif file

def printMaster(entryNumber, entryName, data):
	targetType, targetBank, target = struct.unpack('> 36x B x B B 520x', data)
	targetBank &= 0x0F		# guess about keeping bank in range
	print('%03d: %-20s ' % (entryNumber + 1, entryName), end='')
	if targetType == MasterTargetType.MST_VOICE:
		print('Vc', bankSectionNumberStr(targetBank, target))
	elif targetType == MasterTargetType.MST_PERFORMANCE:
		print('Pf', bankSectionNumberStr(targetBank + 8, target))
			# targetBank + 8 because Performances start in bank USR1
	else:
		if targetType == MasterTargetType.MST_PATTERN:	
			print('Pt', end='')
		else: # targetType == MasterTargetType.MST_SONG
			print('Sg', end='')
		print(' %02d' % (target + 1))

def printPerformance(performanceNumber, entryName, data):
	print('%s %s' % (bankSectionNumberStr(((performanceNumber & 0x0780) >> 7) + 8, performanceNumber & 0x007F),
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
	global catalog

	inputStream.seek(catalog[blockType.ident])
	blockHdr = inputStream.read(BLOCK_HDR_LGTH)
	blockIdData, nEntries = struct.unpack('> 4s 4x I', blockHdr)
	assert blockIdData == blockType.ident, blockType.ident
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
		blockType.printFn(entryNumber, entryName, blockData)	
	print()

def printMotifFile(inputStream):
	global catalog

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
	if len(sys.argv) == 2:
		fileName = sys.argv[1]
		print('file:              ', fileName, '\n', sep='')
		inputStream = open(fileName, 'rb')
		printMotifFile(inputStream)
		inputStream.close()
	else:
		print('need 1 command line arg: motif file name')
