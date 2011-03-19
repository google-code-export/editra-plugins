# -*- coding: utf-8 -*-
# Name: DebugResultsList.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#----------------------------------------------------------------------------#
# Imports
import wx

# Editra Libraries
import eclib

# Local Imports
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class DebuggeeWindow(eclib.OutputBuffer,
                       eclib.ProcessBufferMixin):
    """Debuggee Window"""
    def __init__(self, *args, **kwargs):
        eclib.OutputBuffer.__init__(self, *args, **kwargs)
        eclib.ProcessBufferMixin.__init__(self)
        self.calldebugger = None
        self.restoreautorun = None
        
    def set_mainwindow(self, mw):
        self._mainw = mw

    def AddText(self, text):
        newtext = u"%s\n%s\n" % (self.GetText(), text)
        self.SetText(newtext)
    
    def DoProcessStart(self, cmd=''):
        """Override this method to do any pre-processing before starting
        a processes output.
        @keyword cmd: Command used to start program
        @return: None

        """
        if self.calldebugger:
            wx.CallAfter(self.calldebugger)

    def DoProcessExit(self, code=0):
        """Override this method to do any post processing after the running
        task has exited. Typically this is a good place to call
        L{OutputBuffer.Stop} to stop the buffers timer.
        @keyword code: Exit code of program
        @return: None

        """
        self.AddText(_("Debuggee finished."))
        self.restoreautorun()
        self.Stop()
        