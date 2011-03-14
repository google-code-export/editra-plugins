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
        self.layout("Go", self.OnGo)

        # Attributes
        self.editor = None
        RPDBDEBUGGER.clearframe = self._listCtrl.Clear
        RPDBDEBUGGER.clearstepmarker = self.ClearStepMarker
        RPDBDEBUGGER.setstepmarker = self.SetStepMarker
        RPDBDEBUGGER.restorestepmarker = self.RestoreStepMarker
        RPDBDEBUGGER.selectframe = self._listCtrl.select_frame
        RPDBDEBUGGER.updatestacklist = self.UpdateStackList
        
    def Unsubscription(self):
        RPDBDEBUGGER.clearframe = lambda:None
        RPDBDEBUGGER.clearstepmarker = lambda:None
        RPDBDEBUGGER.setstepmarker = lambda x,y:None
        RPDBDEBUGGER.restorestepmarker = lambda x:None
        RPDBDEBUGGER.selectframe = lambda x:None
        RPDBDEBUGGER.updatestacklist = lambda x:None

    def ClearStepMarker(self):
        if self.editor:
            self.editor.ShowStepMarker(1, show=False)
            self.editor = None
        
    def SetStepMarker(self, fileName, lineNo):
        self.editor = PyToolsUtils.GetEditorOrOpenFile(self._mw, fileName)
        self.editorlineno = lineNo - 1
        self.editor.GotoLine(self.editorlineno)
        self.editor.ShowStepMarker(self.editorlineno, show=True)
        
    def RestoreStepMarker(self, editor):
        if self.editor != editor:
            return
        self.editor.GotoLine(self.editorlineno)
        self.editor.ShowStepMarker(self.editorlineno, show=True)
        
    def UpdateStackList(self, stack):
        self._listCtrl.Clear()
        self._listCtrl.PopulateRows(stack)
        self._listCtrl.RefreshRows()
        
    def OnGo(self, event):
        RPDBDEBUGGER.do_go()