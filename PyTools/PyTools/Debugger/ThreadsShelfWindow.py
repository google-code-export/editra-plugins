# -*- coding: utf-8 -*-
# Name: ThreadsShelfWindow.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id $"
__revision__ = "$Revision $"

#-----------------------------------------------------------------------------#
# Imports
import wx

# Editra Libraries
import util
import eclib
import ed_msg

# Local imports
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.Debugger.ThreadsList import ThreadsList
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation

ID_TOGGLE_BREAKPOINT = wx.NewId()
#-----------------------------------------------------------------------------#

class ThreadsShelfWindow(BaseShelfWindow):
    def __init__(self, parent):
        """Initialize the window"""
        super(ThreadsShelfWindow, self).__init__(parent)
        ctrlbar = self.setup(ThreadsList(self))
        self.layout("Unused", self.OnGo)

        # Attributes
        RPDBDEBUGGER.clearthread = self._listCtrl.Clear
        RPDBDEBUGGER.updatethread = self._listCtrl.update_thread
        RPDBDEBUGGER.updatethreadlist = self.UpdateThreadList
        
    def UpdateThreadList(self, current_thread, threads_list):
        if self._listCtrl.check_suppress_recursion():
            return
        self._listCtrl.Clear()
        self._listCtrl.PopulateRows(current_thread, threads_list)
        self._listCtrl.RefreshRows()
        
    def Unsubscription(self):
        pass

    def OnGo(self, event):
        pass
