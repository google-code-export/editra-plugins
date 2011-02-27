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
import os
import wx
from wx import stc
import copy

# Editra Libraries
import util
import eclib
import ed_msg
from profiler import Profile_Get, Profile_Set
from syntax import syntax
import syntax.synglob as synglob

# Local imports
from PyTools.Common import ToolConfig
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.Debugger.StackFrameList import StackFrameList
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation

MARKER_CALL = [stc.STC_MARK_CHARACTER + ord('C'), wx.WHITE, "#99A9C2"]
MARKER_LINE = [stc.STC_MARK_CHARACTER + ord('L'), wx.WHITE, "#99A9C2"]
MARKER_RETURN = [stc.STC_MARK_CHARACTER + ord('R'), wx.WHITE, "#99A9C2"]
MARKER_EXCEPTION = [stc.STC_MARK_CHARACTER + ord('E'), wx.WHITE, "#99A9C2"]
MARKER_RUNNING = [stc.STC_MARK_CHARACTER + ord('*'), wx.WHITE, "#99A9C2"]

ID_TOGGLE_BREAKPOINT = wx.NewId()
#-----------------------------------------------------------------------------#

class StackFrameShelfWindow(BaseShelfWindow):
    eventmarkermapping = {'running': MARKER_RUNNING, 'call': MARKER_CALL, 'line': MARKER_LINE, 'return': MARKER_RETURN,  'exception': MARKER_EXCEPTION}

    def __init__(self, parent):
        """Initialize the window"""
        super(StackFrameShelfWindow, self).__init__(parent)
        ctrlbar = self.setup(StackFrameList(self))
        ctrlbar.AddStretchSpacer()
        txtentrysize = wx.Size(256, wx.DefaultSize.GetHeight())
        self.textentry = eclib.CommandEntryBase(ctrlbar, wx.ID_ANY, size=txtentrysize,
                                           style=wx.TE_PROCESS_ENTER|wx.WANTS_CHARS)
        ctrlbar.AddControl(self.textentry, wx.ALIGN_RIGHT)
        self.layout("Whatever", self.OnGo)

        # Attributes
        RPDBDEBUGGER.set_seteditormarkers_fn(self.SetEditorMarkers)
        RPDBDEBUGGER.set_unseteditormarkers_fn(self.DeleteEditorMarkers)
        
        self.preveditor = None
        self.prevhandle = None
        
    def SetEditorMarkers(self, fileName, lineNo, event):
        editorlineno = lineNo - 1
        editor = PyToolsUtils.GetEditorOrOpenFile(self._mw, fileName)
        marker = StackFrameShelfWindow.eventmarkermapping[event]
        if editor == self.preveditor:
            editor.MarkerDeleteHandle(self.prevhandle)
        self.preveditor = editor
#        editor.MarkerDefine(37, marker[0], marker[1], marker[2]) 
#        editor.MarkerAdd(lineNo - 1, 37)
        if event != "running":
            editor.MarkerDefine(3, wx.stc.STC_MARK_BACKGROUND, 'white', 'red')
            self.prevhandle = editor.MarkerAdd(editorlineno, 3)
            
    def DeleteEditorMarkers(self):
        if self.preveditor and self.prevhandle:
            self.preveditor.MarkerDeleteHandle(self.prevhandle)

    def Destroy(self):
        pass

    def OnGo(self):
        pass