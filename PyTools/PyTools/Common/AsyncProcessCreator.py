# -*- coding: utf-8 -*-
# Name: AsyncProcessCreator.py
# Purpose: Create asynchronous processes
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" Utility functions """

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
from subprocess import STDOUT

# Local Imports
from PyTools.Common.ProcessCreator import ProcessCreator

# Editra Libraries
import eclib
#-----------------------------------------------------------------------------#

class AsyncProcessCreator(eclib.ProcessThreadBase, ProcessCreator):
    def __init__(self, parent, info, parentPath, cmdline, pythonpath=None):
        eclib.ProcessThreadBase.__init__(self, parent)
        ProcessCreator.__init__(self, info, parentPath, cmdline, pythonpath)
        self.debuggeewindow = parent

    def DoPopen(self):
        return self.createprocess(STDOUT)
        
    def AddText(self, text):
        self.debuggeewindow.AddText(text)