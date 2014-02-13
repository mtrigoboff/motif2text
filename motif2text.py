'''
@author:  Michael Trigoboff
@contact: mtrigoboff@comcast.net
@contact: http://spot.pcc.edu/~mtrigobo
'''

import os.path, sys
import tkinter
from tkinter import BooleanVar, StringVar, ttk
from tkinter.filedialog import askopenfilename

from processFile import blockSpecs, processFile

class CheckBox:
	def __init__(self, label, abbrev, frame):
		self.label =		label
		self.abbrev =		abbrev
		self.variable =		BooleanVar()
		self.checkBtn = 	ttk.Checkbutton(frame, text = label, variable = self.variable,
											command = setCreateBtnState)

# global variables
VERSION = '1.03'
checkBoxes = []
selectedItems = []
motifFilePath = ''
fileName = ''

def setCreateBtnState():
	if len(motifFilePath) == 0:
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
	global motifFilePath, fileName
	motifFilePath = askopenfilename()
	fileName = os.path.basename(motifFilePath)
	fileNameEntryVar.set(fileName)
	setCreateBtnState()

def createTextFn():
	global motifFilePath
	selectedItems = []
	for checkBox in checkBoxes:
		if checkBox.variable.get():
			selectedItems.append(checkBox.abbrev)
	if len(selectedItems) == 0:
		return
	realStdOut = sys.stdout
	textFilePath = motifFilePath + '.txt'
	try:
		textFile = open(textFilePath, 'w')
		sys.stdout = textFile
		processFile(motifFilePath, selectedItems)
		textFile.close()
		# need to enclose textFilePath in "..." so that space chars don't break path
		os.startfile("\"" + textFilePath + "\"")				# open .txt file with default app
		#os.system("notepad.exe \"" + textFilePath + "\"")		#open .txt file with notepad
	except Exception as _:
		fileNameEntryVar.set('problem reading \'%s\'' % fileName)
		motifFilePath = ''
		setCreateBtnState()
		textFile.close()
		os.remove(textFilePath)
	sys.stdout = realStdOut

def helpFn():
	os.startfile('motif2textHelp.pdf')						# open .pdf file with default app

def keyPressFn(kpEvent):
	try:
		fn = {'a' 		:	'allFn()',
			  'n' 		:	'noneFn()',
			  's' 		:	'selectFileFn()',
			  'c' 		:	'createTextFn()',
			  'h'		:	'helpFn()',
			  'F1'		:	'helpFn()',
			  'Escape'	:	'root.quit()',
			  'q' 		:	'root.quit()' } \
			 [kpEvent.keysym]
		eval(fn)
	except KeyError:				# the 'default' case
		return

root = tkinter.Tk()
root.bind_all('<KeyPress>', keyPressFn)

rootFrame = ttk.Frame(root, padding = '12 12 12 12')
rootFrame.pack()

selectItemsFrame = ttk.LabelFrame(rootFrame, text = 'Select Items', padding = '6 0 6 6')
checkBoxFrame = ttk.Frame(selectItemsFrame, padding = '6 6 6 6')
i = 0
for abbrev, blockSpec in blockSpecs.items():
	checkBox = CheckBox(blockSpec.name, abbrev, checkBoxFrame)
	checkBoxes.append(checkBox)
	checkBox.checkBtn.grid(row = int(i % 6), column = int(i / 6), sticky = "w", padx = 6)
	i += 1
checkBoxFrame.pack(side = 'left')
checkBoxBtnsFrame = ttk.Frame(selectItemsFrame, padding = '6 6 6 6')
allBtn = ttk.Button(checkBoxBtnsFrame, text = 'All', command = allFn)
allBtn.grid(row = 0, column = 2, padx = 6, pady = 12)
noneBtn = ttk.Button(checkBoxBtnsFrame, text = 'None', command = noneFn)
noneBtn.grid(row = 1, column = 2, padx = 6, pady = 12)
checkBoxBtnsFrame.pack(side = 'left')
selectItemsFrame.grid(row = 0, column = 0, columnspan = 2)

fileFrame = ttk.Frame(rootFrame, padding = '16 20 12 12')
fileLabel = ttk.Label(fileFrame, text = 'File:  ')
fileLabel.grid(row = 0, column = 0, sticky = 'w')
fileNameEntryVar = StringVar()
fileNameEntry = ttk.Entry(fileFrame, textvariable = fileNameEntryVar, width = 48, state='disabled')
fileNameEntry.grid(row = 0, column = 1, sticky = 'w')
fileFrame.grid(row = 1, column = 0, sticky = 'w', columnspan = 2)

btnsFrame = ttk.Frame(rootFrame, padding = '8 12 12 12')
selectFileBtn = ttk.Button(btnsFrame, text = 'Select File', command = selectFileFn)
selectFileBtn.grid(row = 0, column = 0, sticky = 'w', padx = 6)
createTextBtn = ttk.Button(btnsFrame, text = 'Create Text', command = createTextFn, state = 'disabled')
createTextBtn.grid(row = 0, column = 1, sticky = 'w', padx = 12)
btnsFrame.grid(row = 2, column = 0, padx = 12, sticky = 'ew')

helpBtnFrame = ttk.Frame(rootFrame, padding = '12 12 12 12')
helpBtn = ttk.Button(helpBtnFrame, text = 'Help', command = helpFn)
helpBtn.grid(row = 0, column = 0, sticky = 'e')
helpBtnFrame.grid(row = 2, column = 1, padx = 12, sticky = 'ew')

root.title('Motif 2 Text        v' + VERSION)
root.resizable(False, False)
root.mainloop()
