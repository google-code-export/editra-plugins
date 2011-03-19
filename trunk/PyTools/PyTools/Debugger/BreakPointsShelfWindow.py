# -*- coding: utf-8 -*-
# Name: BreakPointsShelfWindow.py
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
import os.path
import copy
import wx
from wx.stc import STC_INDIC_PLAIN

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
from PyTools.Debugger.BreakPointsList import BreakPointsList
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation

ID_TOGGLE_BREAKPOINT = wx.NewId()
#-----------------------------------------------------------------------------#

class BreakPointsShelfWindow(BaseShelfWindow):
    def __init__(self, parent):
        """Initialize the window"""
        super(BreakPointsShelfWindow, self).__init__(parent)
        ctrlbar = self.setup(BreakPointsList(self))
        ctrlbar.AddStretchSpacer()
        self.layout("Clear", self.OnClear)

        config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        
        # Attributes
        RPDBDEBUGGER.breakpoints = config.get(ToolConfig.TLC_BREAKPOINTS, dict())
        RPDBDEBUGGER.saveandrestorebreakpoints = self.SaveAndRestoreBreakpoints
        
        self._listCtrl.PopulateRows(RPDBDEBUGGER.breakpoints)
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            RPDBDEBUGGER.restorestepmarker(editor)
        RPDBDEBUGGER.load_breakpoints()

        # Editra Message Handlers
        ed_msg.Subscribe(self.OnContextMenu, ed_msg.EDMSG_UI_STC_CONTEXT_MENU)        

    def Unsubscription(self):
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            editor.DeleteAllBreakpoints()
            RPDBDEBUGGER.restorestepmarker(editor)
        ed_msg.Unsubscribe(self.OnContextMenu)
        RPDBDEBUGGER.breakpoints = {}
        RPDBDEBUGGER.saveandrestorebreakpoints = lambda:None
        RPDBDEBUGGER.load_breakpoints()

    def DeleteBreakpoint(self, filepath, lineno):
        if not filepath in RPDBDEBUGGER.breakpoints:
            return None
        linenos = RPDBDEBUGGER.breakpoints[filepath]
        if not lineno in linenos:
            return None
        enabled, exprstr, bpid = linenos[lineno]
        RPDBDEBUGGER.delete_breakpoint(bpid)
        del linenos[lineno]
        if len(linenos) == 0:
            del RPDBDEBUGGER.breakpoints[filepath]
        self.SaveBreakpoints()
        return lineno
        
    def ChangeBreakpoint(self, filepath, lineno, newexprstr, newenabled):
        enabled, exprstr, bpid = RPDBDEBUGGER.breakpoints[filepath][lineno]
        RPDBDEBUGGER.breakpoints[filepath][lineno] = (newenabled, newexprstr, bpid)
        self.SaveBreakpoints()
        
    def SetBreakpoint(self, filepath, lineno, exprstr, enabled):
        if filepath in RPDBDEBUGGER.breakpoints:
            linenos = RPDBDEBUGGER.breakpoints[filepath]
        else:
            linenos = {}
            RPDBDEBUGGER.breakpoints[filepath] = linenos
        bpid = None
        if os.path.isfile(filepath):
            bp = RPDBDEBUGGER.set_breakpoint(filepath, lineno, exprstr)
            if bp:
                bpid = bp.m_id
        linenos[lineno] = (enabled, exprstr, bpid)
        self.SaveBreakpoints()
        return lineno
        
    def RestoreBreakPoints(self):
        self._listCtrl.Clear()
        self._listCtrl.PopulateRows(RPDBDEBUGGER.breakpoints)
        self._listCtrl.RefreshRows()
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            RPDBDEBUGGER.restorestepmarker(editor)

    def SaveBreakpoints(self):
        RPDBDEBUGGER._config[ToolConfig.TLC_BREAKPOINTS] = copy.deepcopy(RPDBDEBUGGER.breakpoints)
    
    def OnContextMenu(self, msg):
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            langid = getattr(editor, 'GetLangId', lambda: -1)()
            ispython = langid == synglob.ID_LANG_PYTHON
            if ispython:
                contextmenumanager = msg.GetData()
                menu = contextmenumanager.GetMenu()
                menu.Append(ID_TOGGLE_BREAKPOINT, _("Toggle Breakpoint"))
                contextmenumanager.AddHandler(ID_TOGGLE_BREAKPOINT, self.toggle_breakpoint)

    def toggle_breakpoint(self, editor, evt):
        filepath = os.path.normcase(editor.GetFileName())
        editorlineno = editor.GetCurrentLineNum()
        lineno = editorlineno + 1
        if not self.DeleteBreakpoint(filepath, lineno):
            self.SetBreakpoint(filepath, lineno, "", True)
        self.RestoreBreakPoints()

    def SaveAndRestoreBreakpoints(self):
        self.SaveBreakpoints()
        self.RestoreBreakPoints()
    
    def OnClear(self, evt):
        RPDBDEBUGGER.breakpoints = {}
        self.SaveAndRestoreBreakpoints()
        Profile_Set(ToolConfig.PYTOOL_CONFIG, RPDBDEBUGGER._config)
