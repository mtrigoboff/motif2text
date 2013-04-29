import struct, sys

FILE_HDR_LGTH =			64
CATALOG_ENTRY_LGTH =	 8
BLOCK_HDR_LGTH =		12
ENTRY_HDR_LGTH =		30

FILE_HDR_ID =		b'YAMAHA-YSFC'
BLOCK_ENTRY_ID =	b'Entr'

catalog = {}

def printEPFM(entryNumber, entryName):
	print('%03d:' % entryNumber, entryName.split(':')[-1])

def printDefault(entryNumber, entryName):
	print('%03d:' % entryNumber, entryName)

blockTypesToPrint = ((b'EPFM',	'Performances',	printEPFM),			\
					 (b'ESNG',	'Songs',		printDefault),		\
					 (b'EPTN',	'Patterns',		printDefault))

def printBlock(blockType):
	blockOffset = catalog[blockType[0]]
	inputStream.seek(blockOffset)
	blockHdr = inputStream.read(BLOCK_HDR_LGTH)
	blockIdData, nEntries = struct.unpack('> 4s 4x I', blockHdr)
	assert blockIdData == blockType[0], blockType[0]
	print(blockType[1])
	for _ in range(0, nEntries):
		entryHdr = inputStream.read(ENTRY_HDR_LGTH)
		entryId, entryLgth, entryNumber = struct.unpack('> 4s I 16x I 2x', entryHdr)
		assert entryId == BLOCK_ENTRY_ID, BLOCK_ENTRY_ID
		entryStrs = inputStream.read(entryLgth - ENTRY_HDR_LGTH + 8)
		entryStrs = entryStrs.decode('ascii')
		entryName = entryStrs.rstrip('\x00').split('\x00')[0]
		blockType[2](entryNumber, entryName)	
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

	for blockType in blockTypesToPrint:
		printBlock(blockType)

# when invoked from the command line
if __name__ == '__main__':
#	print(sys.executable)
	if len(sys.argv) == 2:
		try:
			fileName = sys.argv[1]
			print('file:', fileName)
			inputStream = open(fileName, 'rb')
			printMotifFile(inputStream)
		except Exception as e:
			errorMsg = '--> ' + str(e.args[0])
			print(errorMsg)
			print(errorMsg, file=sys.stderr)
		inputStream.close()
	else:
		print('no args')
