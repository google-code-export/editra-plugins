# -*- coding: utf-8 -*-
# Name: AbstractDebugger.py
# Purpose: Pylint plugin
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

class AbstractDebugger(object):
    def __init__(self, variabledict, filename):
        """ Process dictionary of variables that might be 
        useful to debugger.
        """
        super(AbstractDebugger, self).__init__()

        # Attributes
        self.filename = filename
        self.variabledict = variabledict

    def Debug(self, debugargs):
        """Interface method override to perform the debugging
        """
        raise NotImplementedError

    def _getFileName(self):
        return self.filename
    def _setFileName(self, fname):
        self.filename = fname
    FileName = property(_getFileName, _setFileName)
