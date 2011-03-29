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
import ed_glob
from profiler import Profile_Get, Profile_Set

# Local imports
from PyTools.Common import ToolConfig
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.Debugger.BreakPointsList import BreakPointsList
from PyTools.Debugger.RpdbDebugger import RpdbDebugger
from PyTools.Debugger.MessageHandler import MessageHandler

# Globals
_ = wx.GetTranslation

ID_TOGGLE_BREAKPOINT = wx.NewId()
#-----------------------------------------------------------------------------#

class BreakPointsShelfWindow(BaseShelfWindow):
    def __init__(self, parent):
        """Initialize the window"""
        super(BreakPointsShelfWindow, self).__init__(parent)

        ctrlbar = self.setup(BreakPointsList(self))
        ctrlbar.AddControl(wx.StaticLine(ctrlbar, size=(1, 16), style=wx.LI_VERTICAL),
                           0, wx.ALIGN_LEFT)
        self.addbtn = self.AddPlateButton(u"", ed_glob.ID_ADD, wx.ALIGN_LEFT)
        self.addbtn.ToolTip = wx.ToolTip(_("Set Breakpoint"))
        self.delbtn = self.AddPlateButton(u"", ed_glob.ID_REMOVE, wx.ALIGN_LEFT)
        self.delbtn.ToolTip = wx.ToolTip(_("Delete Breakpoint"))
        self.delallbtn = self.AddPlateButton(u"", ed_glob.ID_DELETE, wx.ALIGN_LEFT)
        self.delallbtn.ToolTip = wx.ToolTip(_("Delete All Breakpoints"))
        self.layout(None, None)

        # Attributes
        bpoints = ToolConfig.GetConfigValue(ToolConfig.TLC_BREAKPOINTS)
        if bpoints is None:
            bpoints = {}
        RpdbDebugger().breakpoints = bpoints
        RpdbDebugger().saveandrestorebreakpoints = self.SaveAndRestoreBreakpoints
        
        self._listCtrl.PopulateRows(RpdbDebugger().breakpoints)
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            RpdbDebugger().restorestepmarker(editor)
        RpdbDebugger().install_breakpoints()
        MessageHandler().AddMenuItem(0, False, ID_TOGGLE_BREAKPOINT, 
                                     _("Toggle Breakpoint"), 
                                     self.ToggleBreakpoint)

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnButton, self.addbtn)
        self.Bind(wx.EVT_BUTTON, self.OnButton, self.delbtn)
        self.Bind(wx.EVT_BUTTON, self.OnClear, self.delallbtn)

    def Unsubscription(self):
        """Cleanup items on destroy"""
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            editor.DeleteAllBreakpoints()
            RpdbDebugger().restorestepmarker(editor)
        RpdbDebugger().breakpoints = {}
        RpdbDebugger().saveandrestorebreakpoints = lambda:None
        RpdbDebugger().install_breakpoints()
        MessageHandler().DeleteMenuItem(0)

    def DeleteBreakpoint(self, filepath, lineno):
        """Remove a breakpoint from the list"""
        if not os.path.isfile(filepath) or \
           not filepath in RpdbDebugger().breakpoints:
            return None
        linenos = RpdbDebugger().breakpoints[filepath]
        if not lineno in linenos:
            return None

        # Delete the breakpoint
        enabled, exprstr = linenos[lineno]
        del linenos[lineno]
        if len(linenos) == 0:
            del RpdbDebugger().breakpoints[filepath]
        RpdbDebugger().delete_breakpoint(filepath, lineno)
        self.SaveBreakpoints()
        return lineno
        
    def SetBreakpoint(self, filepath, lineno, exprstr, enabled):
        """Set a breakpoint in the given file
        @param filepath: normalized file path
        @param lineno: buffer display line number

        """
        if not os.path.isfile(filepath):
            return
        if filepath in RpdbDebugger().breakpoints:
            linenos = RpdbDebugger().breakpoints[filepath]
        else:
            linenos = {}
            RpdbDebugger().breakpoints[filepath] = linenos
        linenos[lineno] = (enabled, exprstr)
        util.Log("[DbgBp][info] SetBreakpoint %s, %d, %s, %s" % \
                 (filepath, lineno, enabled, exprstr))
        if enabled:
            RpdbDebugger().set_breakpoint(filepath, lineno, exprstr)
        self.SaveBreakpoints()
        return lineno
        
    def RestoreBreakPoints(self):
        """Restore breakpoints"""
        self._listCtrl.Clear()
        self._listCtrl.PopulateRows(RpdbDebugger().breakpoints)
        self._listCtrl.RefreshRows()
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            RpdbDebugger().restorestepmarker(editor)

    def SaveBreakpoints(self):
        """Save currently set breakpoints in the user configuration"""
        config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        config[ToolConfig.TLC_BREAKPOINTS] = copy.deepcopy(RpdbDebugger().breakpoints)
        Profile_Set(ToolConfig.PYTOOL_CONFIG, config)
    
    def ToggleBreakpoint(self, editor, event):
        """Toggle the breakpoint at the current line"""
        filepath = os.path.normcase(editor.GetFileName())
        if not self.DeleteBreakpoint(filepath, MessageHandler().ContextLine):
            self.SetBreakpoint(filepath, MessageHandler().ContextLine, "", True)
        self.RestoreBreakPoints()

    def SaveAndRestoreBreakpoints(self):
        """Save an reset breakpoints"""
        self.SaveBreakpoints()
        self.RestoreBreakPoints()

    def OnButton(self, event):
        """Handle control bar button clicks"""
        eobj = event.GetEventObject()
        if eobj is self.addbtn:
            editor = wx.GetApp().GetCurrentBuffer()
            fname = editor.GetFileName()
            if fname:
                fname = os.path.normcase(fname)
                lnum = self.SetBreakpoint(fname, editor.CurrentLine + 1, u"", True)
                editor.SetBreakpoint(lnum)
                self.RestoreBreakPoints()
        elif eobj is self.delbtn:
            for item in self._listCtrl.GetSelectedBreakpoints():
                if len(item) > 1:
                    self.DeleteBreakpoint(item[0], int(item[1]))
                    self.RestoreBreakPoints()
        else:
            event.Skip()

    def OnClear(self, event):
        """Clear all breakpoints"""
        RpdbDebugger().breakpoints = {}
        self.SaveAndRestoreBreakpoints()
