# -*- coding: utf-8 -*-
# Name: DebugResultsList.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id: DebugResultsList.py -1   $"
__revision__ = "$Revision: -1 $"

#----------------------------------------------------------------------------#
# Imports
import wx

# Editra Libraries
import eclib

# Local Imports
from PyTools.Common.PyToolsUtils import PyToolsUtils

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class DebuggeeWindow(eclib.OutputBuffer,
                       eclib.ProcessBufferMixin):
    """Debuggee Window"""
    def __init__(self, *args, **kwargs):
        eclib.OutputBuffer.__init__(self, *args, **kwargs)
        eclib.ProcessBufferMixin.__init__(self)
        
    def set_mainwindow(self, mw):
        self._mainw = mw

    def set_debuggerfn(self, debuggerfn):
        self.debuggerfn = debuggerfn

    def DoProcessStart(self, cmd=''):
        """Override this method to do any pre-processing before starting
        a processes output.
        @keyword cmd: Command used to start program
        @return: None

        """
        if self.debuggerfn:
            wx.CallAfter(self.debuggerfn)
