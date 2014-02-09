'''
@author:  Michael Trigoboff
@contact: mtrigoboff@comcast.net
@contact: http://spot.pcc.edu/~mtrigobo
'''

import os.path
import tkinter
from tkinter import BooleanVar, StringVar, ttk
from tkinter.filedialog import askopenfilename

from processFile import blockSpecs, processFile


class CheckBox:
	def __init__(self, label, abbrev, frame):
		self.label =		label
		self.abbrev =		abbrev
		self.variable =		BooleanVar()
		self.checkBtn = 	ttk.Checkbutton(frame, text = label, variable = self.variable)

def allFn():
	for checkBox in checkBoxes:
		checkBox.variable.set(True)

def noneFn():
	for checkBox in checkBoxes:
		checkBox.variable.set(False)

def selectFileFn():
	global filePath
	filePath = askopenfilename()
	fileName = os.path.basename(filePath)
	fileNameEntryVar.set(fileName)
	if len(filePath) != 0:
		createTextBtn['state'] = 'enabled'

def createTextFn():
	for checkBox in checkBoxes:
		if checkBox.variable.get():
			selectedItems.append(checkBox.abbrev)
	processFile(filePath, selectedItems)

def helpFn():
	pass

def keypressFn(kpEvent):
	try:
		fn = {'Escape'	:	'exit()',			# exit() raises SystemExitif
			  'q' 		:	'exit()' } \
			 [kpEvent.keysym]
		eval(fn)
	except KeyError:				# the 'default' case
		return

checkBoxes = []
selectedItems = []
filePath = ''
fileName = ''

root = tkinter.Tk()
root.bind_all('<KeyPress>', keypressFn)

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

root.title("Motif 2 Text")
root.resizable(False, False)
root.mainloop()
