# -*- coding: utf-8 -*-

# A simple setup script to create an executable using Tkinter. This also
# demonstrates the method for creating a Windows executable that does not have
# an associated console.
#
# SimpleTkApp.py is a very simple type of Tkinter application
#
# Run the build process by running the command 'python setup.py build'
#
# If everything works well you should find a subdirectory in the build
# subdirectory that contains the files needed to run the application

# mlt: this is a slightly-edited copy of:
#		C:\Python33\Lib\site-packages\cx_Freeze\samples\Tkinter\setup.py

# mlt: needs 1 cmd line arg: build

import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

executables = [
    Executable('motif2text.py', base=base)
]

setup(name='simple_Tkinter',
      version='0.1',
      description='Sample cx_Freeze Tkinter script',
      executables=executables
      )
