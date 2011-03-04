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
        self.layout("Whatever", self.OnGo)

        # Attributes
        RPDBDEBUGGER.set_seteditormarkers_fn(self.SetEditorMarkers)
        RPDBDEBUGGER.set_removeeditormarkers_fn(self.RemoveEditorMarkers)
        
        self.triggeredbps = {}
        
    def SetEditorMarkers(self, fileName, lineNo):
        editor = PyToolsUtils.GetEditorOrOpenFile(self._mw, fileName)
        editorlineno = lineNo - 1
        editor.GotoLine(editorlineno)
        handle = editor.SetBreakpointTriggered(editorlineno)
        linenos = self.triggeredbps.get(editor)
        if not linenos:
            linenos = {}
            self.triggeredbps[editor] = linenos                
        if handle == -1:
            linenos[editorlineno] = linenos[editorlineno] + 1
        else:
            linenos[editorlineno] = 1

    def RemoveEditorMarkers(self, fileName, editorlineno):
        editor = PyToolsUtils.GetEditorForFile(self._mw, fileName)
        if not editor:
            return
        linenos = self.triggeredbps.get(editor)
        if not linenos:
            return
        numberthreads = linenos.get(editorlineno)
        if not numberthreads:
            return
        numberthreads = numberthreads - 1
        if numberthreads:
            linenos[editorlineno] = numberthreads
            return
        del linenos[editorlineno]
        editor.DeleteBreakpoint(editorlineno)        
    
    def Unsubscription(self):
        pass

    def OnGo(self):
        pass