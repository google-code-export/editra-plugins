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
import wx.lib.mixins.listctrl as mixins

# Editra Imports
import ed_msg
import eclib.outbuff as outbuff
import util

# Local Imports
from PyTools.Common.PyToolsUtils import PyToolsUtils

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class DebuggeeWindow(outbuff.OutputBuffer,
                       outbuff.ProcessBufferMixin,
                       outbuff.ProcessThreadBase):
    """Debuggee Window"""
    def __init__(self, *args, **kwargs):
        outbuff.OutputBuffer.__init__(self, *args, **kwargs)
        outbuff.ProcessBufferMixin.__init__(self)
        outbuff.ProcessThreadBase.__init__(self, args[0])
        self.process = None
        
    def set_mainwindow(self, mw):
        self._mainw = mw

    def setprocess(self, process):
        self.process = process

    def DoPopen(self):
        """Open the process
        @return: subprocess.Popen instance

        """
        return self.process
