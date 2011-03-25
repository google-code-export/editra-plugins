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
from profiler import Profile_Get, Profile_Set

# Local imports
from PyTools.Common import ToolConfig
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.Debugger.BreakPointsList import BreakPointsList
from PyTools.Debugger import RPDBDEBUGGER
from PyTools.Debugger import MESSAGEHANDLER

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

        # Attributes
        RPDBDEBUGGER.breakpoints = ToolConfig.GetConfigValue(ToolConfig.TLC_BREAKPOINTS)
        RPDBDEBUGGER.saveandrestorebreakpoints = self.SaveAndRestoreBreakpoints
        
        self._listCtrl.PopulateRows(RPDBDEBUGGER.breakpoints)
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            RPDBDEBUGGER.restorestepmarker(editor)
        RPDBDEBUGGER.install_breakpoints()
        MESSAGEHANDLER.AddMenuItem(0, False, ID_TOGGLE_BREAKPOINT, _("Toggle Breakpoint"), self.toggle_breakpoint)

    def Unsubscription(self):
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            editor.DeleteAllBreakpoints()
            RPDBDEBUGGER.restorestepmarker(editor)
        RPDBDEBUGGER.breakpoints = {}
        RPDBDEBUGGER.saveandrestorebreakpoints = lambda:None
        RPDBDEBUGGER.install_breakpoints()
        MESSAGEHANDLER.DeleteMenuItem(0)

    def DeleteBreakpoint(self, filepath, lineno):
        if not os.path.isfile(filepath):
            return None
        if not filepath in RPDBDEBUGGER.breakpoints:
            return None
        linenos = RPDBDEBUGGER.breakpoints[filepath]
        if not lineno in linenos:
            return None
        enabled, exprstr = linenos[lineno]
        del linenos[lineno]
        if len(linenos) == 0:
            del RPDBDEBUGGER.breakpoints[filepath]
        RPDBDEBUGGER.delete_breakpoint(filepath, lineno)
        self.SaveBreakpoints()
        return lineno
        
    def SetBreakpoint(self, filepath, lineno, exprstr, enabled):
        if not os.path.isfile(filepath):
            return
        if filepath in RPDBDEBUGGER.breakpoints:
            linenos = RPDBDEBUGGER.breakpoints[filepath]
        else:
            linenos = {}
            RPDBDEBUGGER.breakpoints[filepath] = linenos
        linenos[lineno] = (enabled, exprstr)
        util.Log("[DbgBp][info] %s, %d, %s, %s" % (filepath, lineno, enabled, exprstr))
        if enabled:
            RPDBDEBUGGER.set_breakpoint(filepath, lineno, exprstr)
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
        config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        config[ToolConfig.TLC_BREAKPOINTS] = copy.deepcopy(RPDBDEBUGGER.breakpoints)
        Profile_Set(ToolConfig.PYTOOL_CONFIG, config)
    
    def toggle_breakpoint(self, editor, event):
        filepath = os.path.normcase(editor.GetFileName())
        if not self.DeleteBreakpoint(filepath, MESSAGEHANDLER.contextlineno):
            self.SetBreakpoint(filepath, MESSAGEHANDLER.contextlineno, "", True)
        self.RestoreBreakPoints()

    def SaveAndRestoreBreakpoints(self):
        self.SaveBreakpoints()
        self.RestoreBreakPoints()
    
    def OnClear(self, event):
        RPDBDEBUGGER.breakpoints = {}
        self.SaveAndRestoreBreakpoints()
