'''
@author:  Michael Trigoboff
@contact: mtrigoboff@comcast.net
@contact: http://spot.pcc.edu/~mtrigobo
'''

import configparser
import os.path
import sys
from tkinter import BooleanVar, StringVar, ttk
import tkinter
from tkinter.filedialog import askopenfilename

from printMotifFile import blockSpecs, printMotifFile, VERSION as PMF_VERSION


class CheckBox:
	def __init__(self, label, underlineIndex, abbrev, frame, state):
		self.label =		label
		self.abbrev =		abbrev
		self.variable =		BooleanVar()
		self.checkBtn = 	ttk.Checkbutton(frame, text = label, variable = self.variable,
											command = setCreateBtnState, underline = underlineIndex)
		checkBoxShortcuts[label[underlineIndex].lower()] = self
		self.variable.set(state)

# global variables
VERSION =				'1.05'
checkBoxes =			[]
checkBoxShortcuts = 	{}

def launchFile(filePath):			# launch file with default app for that file type
	# need to enclose filePath in "..." so that space chars don't break path
	filePath = '\"' + filePath + '\"'
	# open file with default app
	if sys.platform == 'win32' or sys.platform == 'win64':		# windows
		os.startfile(filePath)
	else:														# mac, linux
		os.system("open " + filePath)
	#os.system("notepad.exe \"" + textFilePath + "\"")			#open .txt file with notepad

def setCreateBtnState():
	if len(motifFileDir) == 0:
		createTextBtn['state'] = 'disabled'
	else:
		atLeastOneChecked = False
		for checkBox in checkBoxes:
			if checkBox.variable.get():
				atLeastOneChecked = True
		if atLeastOneChecked:
			createTextBtn['state'] = 'enabled'
		else:
			createTextBtn['state'] = 'disabled'		

def allFn():
	for checkBox in checkBoxes:
		checkBox.variable.set(True)
	setCreateBtnState()

def noneFn():
	for checkBox in checkBoxes:
		checkBox.variable.set(False)
	setCreateBtnState()		

def selectFileFn():
	global motifFileDir, motifFileName
	
	motifFilePath = askopenfilename(initialdir = motifFileDir)
	if motifFilePath == '':								# user hit Cancel
		return
	# can't use realpath until here because it turns '' into something else, disabling Cancel
	motifFilePath = os.path.realpath(motifFilePath)
		# use realpath so that path separators are platform-specific, e.g. Windows '\'
	motifFileDir = os.path.dirname(motifFilePath)
	motifFileName = os.path.basename(motifFilePath)
	fileNameEntryVar.set(motifFileName)
	setCreateBtnState()

def createTextFn():
	global motifFileDir, motifFileName
	selectedItems = []
	for checkBox in checkBoxes:
		if checkBox.variable.get():
			selectedItems.append(checkBox.abbrev)
	if len(selectedItems) == 0:
		return
	realStdOut = sys.stdout
	motifFilePath = os.path.join(motifFileDir, motifFileName)
	textFilePath = motifFilePath + '.txt'
	try:
		textFile = open(textFilePath, 'w')
		sys.stdout = textFile
		printMotifFile(motifFilePath, selectedItems)
		textFile.close()
		launchFile(textFilePath)
	except Exception as _:
		fileNameEntryVar.set('problem reading \'%s\'' % motifFileName)
		motifFileDir = ''
		motifFileName = ''
		setCreateBtnState()
		if not textFile.closed:
			textFile.close()
		os.remove(textFilePath)
	sys.stdout = realStdOut

def helpFn():
	launchFile('motif2textHelp.pdf')

def checkBoxKeyboardShortcutFn(ch):
	try:
		checkBox = checkBoxShortcuts[ch]
		checkBox.variable.set(not checkBox.variable.get())
		setCreateBtnState()
	except KeyError:
		pass

def keyPressFn(kpEvent):
	try:
		fn = {'a' 		:	'allFn()',
			  'c'		:	'checkBoxKeyboardShortcutFn(kpEvent.keysym)',
			  'e'		:	'checkBoxKeyboardShortcutFn(kpEvent.keysym)',
			  'f'		:	'selectFileFn()',
			  'g'		:	'checkBoxKeyboardShortcutFn(kpEvent.keysym)',
			  'l'		:	'checkBoxKeyboardShortcutFn(kpEvent.keysym)',
			  'm'		:	'checkBoxKeyboardShortcutFn(kpEvent.keysym)',
			  'h'		:	'helpFn()',
			  'n' 		:	'noneFn()',
			  'o'		:	'checkBoxKeyboardShortcutFn(kpEvent.keysym)',
			  'p'		:	'checkBoxKeyboardShortcutFn(kpEvent.keysym)',
			  'q' 		:	'root.quit()',
			  'r'		:	'checkBoxKeyboardShortcutFn(kpEvent.keysym)',
			  's'		:	'checkBoxKeyboardShortcutFn(kpEvent.keysym)',
			  't' 		:	'createTextFn()',
			  'v'		:	'checkBoxKeyboardShortcutFn(kpEvent.keysym)',
			  'w'		:	'checkBoxKeyboardShortcutFn(kpEvent.keysym)',
			  'x'		:	'checkBoxKeyboardShortcutFn(kpEvent.keysym)',
			  'F1'		:	'helpFn()',
			  'Escape'	:	'root.quit()' } \
			 [kpEvent.keysym]
		eval(fn)
	except KeyError:				# the 'default' case
		pass

def setupGUI(checkBoxStates):
	global createTextBtn, fileNameEntryVar

	root.bind_all('<KeyPress>', keyPressFn)
	rootFrame = ttk.Frame(root, padding = '12 12 12 12')
	rootFrame.pack()

	selectItemsFrame = ttk.LabelFrame(rootFrame, text = 'Select Items', padding = '6 0 6 6')
	checkBoxFrame = ttk.Frame(selectItemsFrame, padding = '6 6 6 6')
	i = 0
	for bsItem, cbState in zip(blockSpecs.items(), checkBoxStates):
		checkBox = CheckBox(bsItem[1].name, bsItem[1].underline, bsItem[0], checkBoxFrame, cbState)
		checkBoxes.append(checkBox)
		checkBox.checkBtn.grid(row = int(i % 6), column = int(i / 6), sticky = "w", padx = 6)
		i += 1
	checkBoxFrame.pack(side = 'left')
	checkBoxBtnsFrame = ttk.Frame(selectItemsFrame, padding = '6 6 6 6')
	allBtn = ttk.Button(checkBoxBtnsFrame, text = 'All', command = allFn, underline = 0)
	allBtn.grid(row = 0, column = 2, padx = 6, pady = 12)
	noneBtn = ttk.Button(checkBoxBtnsFrame, text = 'None', command = noneFn, underline = 0)
	noneBtn.grid(row = 1, column = 2, padx = 6, pady = 12)
	checkBoxBtnsFrame.pack(side = 'left')
	selectItemsFrame.grid(row = 0, column = 0, columnspan = 2)
	
	fileFrame = ttk.Frame(rootFrame, padding = '16 20 12 12')
	fileLabel = ttk.Label(fileFrame, text = 'File:  ')
	fileLabel.grid(row = 0, column = 0, sticky = 'w')
	fileNameEntryVar = StringVar()
	fileNameEntry = ttk.Entry(fileFrame, textvariable = fileNameEntryVar, width = 48, state='disabled')
	fileNameEntryVar.set(motifFileName)
	fileNameEntry.grid(row = 0, column = 1, sticky = 'w')
	fileFrame.grid(row = 1, column = 0, sticky = 'w', columnspan = 2)
	
	btnsFrame = ttk.Frame(rootFrame, padding = '8 12 12 12')
	selectFileBtn = ttk.Button(btnsFrame, text = 'Select File', command = selectFileFn, underline = 7)
	selectFileBtn.grid(row = 0, column = 0, sticky = 'w', padx = 6)
	createTextBtn = \
		ttk.Button(btnsFrame, text = 'Create Text', command = createTextFn, state = 'disabled', underline = 7)
	createTextBtn.grid(row = 0, column = 1, sticky = 'w', padx = 12)
	btnsFrame.grid(row = 2, column = 0, padx = 12, sticky = 'ew')
	
	helpBtnFrame = ttk.Frame(rootFrame, padding = '12 12 12 12')
	helpBtn = ttk.Button(helpBtnFrame, text = 'Help', command = helpFn, underline = 0)
	helpBtn.grid(row = 0, column = 0, sticky = 'e')
	helpBtnFrame.grid(row = 2, column = 1, padx = 12, sticky = 'ew')
	
	setCreateBtnState()

def getAppDirectory():									# returns directory app is in
	# see http://cx-freeze.readthedocs.org/en/latest/faq.html
	if getattr(sys, 'frozen', False):					# running in version created by cx_Freeze
		appDir = os.path.dirname(sys.executable)
	else:												# running in normal Python mode
		appDir = os.path.dirname(__file__)
	return os.path.realpath(appDir)
		# realpath to get os-specific path separators, e.g. '\' for Windows

def run():
	global root					# required by 'Escape' and 'q' keyboard shortcuts
	global motifFileDir, motifFileName
	
	STATE_FILE_NAME =		'motif2text.ini'
	STATE_SECTION_NAME =	'APP_STATE'
	WN_POSN_KEY = 			'WindowPosition'
	MOTIF_FILE_DIR_KEY =	'MotifFileDir'
	MOTIF_FILE_NAME_KEY =	'MotifFileName'
	CHECK_BOX_STATES = 		'CheckBoxStates'
	
	config = configparser.ConfigParser()
	config.optionxform = str		# preserve case in key names

	# set up app state
	stateFilePath = os.path.join(getAppDirectory(), STATE_FILE_NAME)
	if os.path.isfile(stateFilePath):
		config.read(stateFilePath)
		stateSection = config[STATE_SECTION_NAME]
		windowPosn = \
			[int(coord) for coord in stateSection[WN_POSN_KEY].replace(' ', '').split(',')]
		motifFileDir = stateSection[MOTIF_FILE_DIR_KEY]
		motifFileName = stateSection[MOTIF_FILE_NAME_KEY]
		if not os.path.isdir(motifFileDir):
			motifFileDir = ''
			motifFileName = ''
		elif not os.path.isfile(os.path.join(motifFileDir, motifFileName)):
			motifFileName = ''
		strToBool = lambda strg : strg == 'True'
		checkBoxStates = \
			[strToBool(val) for val in stateSection[CHECK_BOX_STATES].replace(' ', '').split(',')]
	else:
		windowPosn = (40, 40)
		motifFileDir = ''
		motifFileName = ''
		checkBoxStates = [False] * len(blockSpecs.items())
	
	root = tkinter.Tk()											# open window
	root.geometry('+%d+%d' % (windowPosn[0], windowPosn[1]))	# position window (x, y)
	
	setupGUI(checkBoxStates)

	root.title('motif2text    v%s(%s)' % (VERSION, PMF_VERSION))
	root.resizable(False, False)
	root.mainloop()
	
	config[STATE_SECTION_NAME] = { \
		WN_POSN_KEY			:	'%d, %d' % (root.winfo_x(), root.winfo_y()),
		MOTIF_FILE_DIR_KEY	:	motifFileDir,
		MOTIF_FILE_NAME_KEY	:	motifFileName,
		CHECK_BOX_STATES	:	str([bool(cb.variable.get()) for cb in checkBoxes]).strip('[]')}
	with open(stateFilePath, 'w') as configFile:
		config.write(configFile)

if __name__ == '__main__':
	run()
