# -*- coding: utf-8 -*-
# Name: StackThreadShelfWindow.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx

# Editra Libraries
import eclib

# Local imports
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.Debugger.StackFrameList import StackFrameList
from PyTools.Debugger.ThreadsList import ThreadsList
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class StackThreadShelfWindow(BaseShelfWindow):
    def __init__(self, parent):
        """Initialize the window"""
        super(StackThreadShelfWindow, self).__init__(parent)

        bstyle = eclib.SEGBOOK_STYLE_NO_DIVIDERS|eclib.SEGBOOK_STYLE_LABELS
        # Attributes
        self.prevstack = None
        self.current_thread = None
        self.threads_list = None        
        self._nb = eclib.SegmentBook(self, style=bstyle)        
        self._stackframe = StackFrameList(self._nb)
        self._threads = ThreadsList(self._nb)
        
        # Setup
        self._InitImageList()
        self._nb.AddPage(self._stackframe, _("Stack Frame"), img_id=0)
        self._nb.AddPage(self._threads, _("Threads"), img_id=0)
        ctrlbar = self.setup(self._nb, self._stackframe,
                             self._threads)
        ctrlbar.AddStretchSpacer()
        self.layout()
                
        # Debugger Attributes
        RPDBDEBUGGER.clearframe = self.ClearStackList
        RPDBDEBUGGER.selectframe = self._stackframe.select_frame
        RPDBDEBUGGER.updatestacklist = self.UpdateStackList
        RPDBDEBUGGER.clearthread = self.ClearThreadList
        RPDBDEBUGGER.updatethread = self._threads.update_thread
        RPDBDEBUGGER.updatethreadlist = self.UpdateThreadList

        RPDBDEBUGGER.update_stack()
        current_thread, threads_list = RPDBDEBUGGER.get_thread_list()
        self.UpdateThreadList(current_thread, threads_list)

    def Unsubscription(self):
        """Cleanup on Destroy"""
        RPDBDEBUGGER.clearframe = lambda:None
        RPDBDEBUGGER.selectframe = lambda x:None
        RPDBDEBUGGER.updatestacklist = lambda x:None
        RPDBDEBUGGER.clearthread = lambda:None
        RPDBDEBUGGER.updatethread = lambda x,y,z:None
        RPDBDEBUGGER.updatethreadlist = lambda x,y:None

    def UpdateStackList(self, stack):
        """Update stack information ListCtrl"""
        if not stack or self.prevstack == stack:
            return
        self.prevstack = stack
        self._stackframe.Clear()
        self._stackframe.PopulateRows(stack)
        self._stackframe.RefreshRows()

    def ClearStackList(self):
        """Clear the ListCtrl"""
        self.prevstack = None
        self._stackframe.Clear()

    def UpdateThreadList(self, current_thread, threads_list):
        if not threads_list:
            return
        if self.current_thread == current_thread and self.threads_list == threads_list:
            return
        self.current_thread = current_thread
        self.threads_list = threads_list
        self._threads.Clear()
        self._threads.PopulateRows(current_thread, threads_list)
        self._threads.RefreshRows()
        
    def ClearThreadList(self):
        self.current_thread = None
        self.threads_list = None
        self._threads.Clear()
       