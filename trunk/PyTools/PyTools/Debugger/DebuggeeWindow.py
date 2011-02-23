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

# Editra Imports
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
