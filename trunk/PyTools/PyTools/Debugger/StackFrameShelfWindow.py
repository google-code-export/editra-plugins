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
        RPDBDEBUGGER.seteditormarkers = self.SetEditorMarkers
        RPDBDEBUGGER.removeeditormarkers = self.RemoveEditorMarkers
        RPDBDEBUGGER.selectframe = self._listCtrl.select_frame
        RPDBDEBUGGER.updatestacklist = self.UpdateStackList
        
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
        breakpoints = RPDBDEBUGGER.getbreakpoints()
        linenos = breakpoints.get(fileName)
        if not linenos:
            return
        res = linenos.get(editorlineno + 1)
        if not res:
            return
        enabled, exprstr, bpid = res
        if enabled:
            editor.SetBreakpoint(editorlineno)
        else:
            editor.SetBreakpointDisabled(editorlineno)

    def UpdateStackList(self, stack):
        self._listCtrl.Clear()
        self._listCtrl.PopulateRows(stack)
        self._listCtrl.RefreshRows()
        
    def Unsubscription(self):
        pass

    def OnGo(self, event):
        index = RPDBDEBUGGER.get_frameindex()
        if index is None:
            return
        filepath, editorlineno = self._listCtrl.GetFileNameEditorLineNo(index)
        RPDBDEBUGGER.do_go(filepath, editorlineno)