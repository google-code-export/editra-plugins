# -*- coding: utf-8 -*-
# Name: AbstractDebugger.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" Debugger module """

__version__ = "0.2"
__author__ = "Mike Rans"
__svnid__ = "$Id: AbstractDebugger.py 1001 2010-12-13 21:16:53Z rans@email.com $"
__revision__ = "$Revision: 1001 $"

#-----------------------------------------------------------------------------#
# Imports
from Common.PyToolsUtils import RunProcInThread

#-----------------------------------------------------------------------------#

class AbstractDebugger(object):
    def __init__(self, variabledict, filename):
        """ Process dictionary of variables that might be
        useful to debugger.
        """
        super(AbstractDebugger, self).__init__()

        # Attributes
        self.filename = filename
        self.variabledict = variabledict

    def DoDebug(self):
        """Interface method override to perform the debug
        and return a list of tuples.
        @return: [ (Filepath), ]

        """
        raise NotImplementedError

    def Debug(self, callback):
        """Asynchronous method to perform module find
        @param callback: callable(data) callback to receive data

        """
        worker = RunProcInThread(self.DoDebug, callback, "Debug")
        worker.start()

    def _getFileName(self):
        return self.filename
    def _setFileName(self, fname):
        self.filename = fname
    FileName = property(_getFileName, _setFileName)
