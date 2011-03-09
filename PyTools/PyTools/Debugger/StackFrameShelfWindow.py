# -*- coding: utf-8 -*-
# Name: StackFrameShelfWindow.py
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
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.Debugger.StackFrameList import StackFrameList
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation

ID_TOGGLE_BREAKPOINT = wx.NewId()
#-----------------------------------------------------------------------------#

class StackFrameShelfWindow(BaseShelfWindow):
    def __init__(self, parent):
        """Initialize the window"""
        super(StackFrameShelfWindow, self).__init__(parent)
        ctrlbar = self.setup(StackFrameList(self))
        ctrlbar.AddStretchSpacer()
        txtentrysize = wx.Size(256, wx.DefaultSize.GetHeight())
        self.textentry = eclib.CommandEntryBase(ctrlbar, wx.ID_ANY, size=txtentrysize,
                                           style=wx.TE_PROCESS_ENTER|wx.WANTS_CHARS)
        ctrlbar.AddControl(self.textentry, wx.ALIGN_RIGHT)
        self.layout("Go", self.OnGo)

        # Attributes
        RPDBDEBUGGER.clearframe = self._listCtrl.Clear
        RPDBDEBUGGER.clearstepmarker = self.ClearStepMarker
        RPDBDEBUGGER.setstepmarker = self.SetStepMarker
        RPDBDEBUGGER.selectframe = self._listCtrl.select_frame
        RPDBDEBUGGER.updatestacklist = self.UpdateStackList
        
    def ClearStepMarker(self):
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            editor.ShowStepMarker(1, show=False)
        
    def SetStepMarker(self, fileName, lineNo):
        editor = PyToolsUtils.GetEditorOrOpenFile(self._mw, fileName)
        editorlineno = lineNo - 1
        editor.GotoLine(editorlineno)
        editor.ShowStepMarker(editorlineno, show=True)
        
    def UpdateStackList(self, stack):
        self._listCtrl.Clear()
        self._listCtrl.PopulateRows(stack)
        self._listCtrl.RefreshRows()
        
    def Unsubscription(self):
        pass

    def OnGo(self, event):
        RPDBDEBUGGER.do_go()