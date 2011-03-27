# -*- coding: utf-8 -*-
# Name: StackFrameShelfWindow.py
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

# Local imports
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.Debugger.StackFrameList import StackFrameList
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class StackFrameShelfWindow(BaseShelfWindow):
    def __init__(self, parent):
        """Initialize the window"""
        super(StackFrameShelfWindow, self).__init__(parent)

        # Setup
        ctrlbar = self.setup(StackFrameList(self))
        self.layout()

        # Attributes
        RPDBDEBUGGER.clearframe = self.ClearStackList
        RPDBDEBUGGER.selectframe = self._listCtrl.select_frame
        RPDBDEBUGGER.updatestacklist = self.UpdateStackList

        self.prevstack = None
        RPDBDEBUGGER.update_stack()

    def Unsubscription(self):
        """Cleanup on Destroy"""
        RPDBDEBUGGER.clearframe = lambda:None
        RPDBDEBUGGER.selectframe = lambda x:None
        RPDBDEBUGGER.updatestacklist = lambda x:None

    def UpdateStackList(self, stack):
        """Update stack information ListCtrl"""
        if not stack or self.prevstack == stack:
            return
        self.prevstack = stack
        self._listCtrl.Clear()
        self._listCtrl.PopulateRows(stack)
        self._listCtrl.RefreshRows()

    def ClearStackList(self):
        """Clear the ListCtrl"""
        self.prevstack = None
        self._listCtrl.Clear()
