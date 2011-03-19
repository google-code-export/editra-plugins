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
#-----------------------------------------------------------------------------#

class ThreadsShelfWindow(BaseShelfWindow):
    def __init__(self, parent):
        """Initialize the window"""
        super(ThreadsShelfWindow, self).__init__(parent)
        ctrlbar = self.setup(ThreadsList(self))
        self.layout()
                
        # Attributes
        self.current_thread = None
        self.threads_list = None
        RPDBDEBUGGER.clearthread = self.ClearThreadList
        RPDBDEBUGGER.updatethread = self._listCtrl.update_thread
        RPDBDEBUGGER.updatethreadlist = self.UpdateThreadList

        current_thread, threads_list = RPDBDEBUGGER.get_thread_list()
        self.UpdateThreadList(current_thread, threads_list)

    def Unsubscription(self):
        RPDBDEBUGGER.clearthread = lambda:None
        RPDBDEBUGGER.updatethread = lambda x,y,z:None
        RPDBDEBUGGER.updatethreadlist = lambda x,y:None

    def UpdateThreadList(self, current_thread, threads_list):
        if self.current_thread == current_thread and self.threads_list == threads_list:
            return
        self.current_thread = current_thread
        self.threads_list = threads_list
        self._listCtrl.Clear()
        self._listCtrl.PopulateRows(current_thread, threads_list)
        self._listCtrl.RefreshRows()
        
    def ClearThreadList(self):
        self.current_thread = None
        self.threads_list = None
        self._listCtrl.Clear()
        
    def OnGo(self, event):
        pass
