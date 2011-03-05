# -*- coding: utf-8 -*-
# Name: BreakPointsShelfWindow.py
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
from wx.stc import STC_INDIC_PLAIN
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
        txtentrysize = wx.Size(256, wx.DefaultSize.GetHeight())
        self.textentry = eclib.CommandEntryBase(ctrlbar, wx.ID_ANY, size=txtentrysize,
                                           style=wx.TE_PROCESS_ENTER|wx.WANTS_CHARS)
        ctrlbar.AddControl(self.textentry, wx.ALIGN_RIGHT)
        self.layout("Clear", self.OnClear)

        # Attributes
        self._config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())

        # Editra Message Handlers
        ed_msg.Subscribe(self.OnFileLoad, ed_msg.EDMSG_FILE_OPENED)
        ed_msg.Subscribe(self.OnFileSave, ed_msg.EDMSG_FILE_SAVED)
        ed_msg.Subscribe(self.OnPageChanged, ed_msg.EDMSG_UI_NB_CHANGED)
        ed_msg.Subscribe(self.OnContextMenu, ed_msg.EDMSG_UI_STC_CONTEXT_MENU)
        
        self.breakpoints = self._config.get(ToolConfig.TLC_BREAKPOINTS, dict())
        self._listCtrl.PopulateRows(self.breakpoints)
        RPDBDEBUGGER.getbreakpoints = self.GetBreakPoints
        RPDBDEBUGGER.checkterminate = self.CheckTerminate

    def GetBreakPoints(self):
        return self.breakpoints

    def DeleteBreakpoint(self, filepath, lineno):
        if not filepath in self.breakpoints:
            return None
        linenos = self.breakpoints[filepath]
        if not lineno in linenos:
            return None
        enabled, exprstr, bpid = linenos[lineno]
        RPDBDEBUGGER.delete_breakpoint(bpid)
        del linenos[lineno]
        if len(linenos) == 0:
            del self.breakpoints[filepath]
        self.SaveBreakpoints()
        return lineno
        
    def ChangeBreakpoint(self, filepath, lineno, newexprstr, newenabled):
        enabled, exprstr, bpid = self.breakpoints[filepath][lineno]
        self.breakpoints[filepath][lineno] = (newenabled, newexprstr, bpid)
        self.SaveBreakpoints()
        
    def SetBreakpoint(self, filepath, lineno, exprstr, enabled):
        if filepath in self.breakpoints:
            linenos = self.breakpoints[filepath]
        else:
            linenos = {}
            self.breakpoints[filepath] = linenos
        bp = RPDBDEBUGGER.set_breakpoint(filepath, lineno, exprstr)
        bpid = None
        if bp:
            bpid = bp.m_id
        linenos[lineno] = (enabled, exprstr, bpid)
        self.SaveBreakpoints()
        return lineno
        
    def RestoreBreakPoints(self):
        self._listCtrl.Clear()
        self._listCtrl.PopulateRows(self.breakpoints)
        self._listCtrl.RefreshRows()

    def SaveBreakpoints(self):
        self._config[ToolConfig.TLC_BREAKPOINTS] = copy.deepcopy(self.breakpoints)
        Profile_Set(ToolConfig.PYTOOL_CONFIG, self._config)
    
    def CheckTerminate(self, filepath, lineno):
        if self._config.get(ToolConfig.TLC_EXITHANDLE, False):
            return False
        if filepath.find("rpdb2.py") == -1:
            return False
        bpinfile = self.breakpoints.get(filepath)
        if not bpinfile:
            return True
        if not bpinfile.get(lineno):
            return True
        return False
        
    def Unsubscription(self):
        ed_msg.Unsubscribe(self.OnFileLoad)
        ed_msg.Unsubscribe(self.OnFileSave)
        ed_msg.Unsubscribe(self.OnPageChanged)
        ed_msg.Unsubscribe(self.OnContextMenu)

    def UpdateForEditor(self, editor, force=False):
        langid = getattr(editor, 'GetLangId', lambda: -1)()
        ispython = langid == synglob.ID_LANG_PYTHON
        self.taskbtn.Enable(ispython)

        self.SaveBreakpoints()
        self.RestoreBreakPoints()
            
        if force or not self._hasrun:
#            fname = getattr(editor, 'GetFileName', lambda: u"")()
#            if ispython:
#                self._lbl.SetLabel(fname)
#            else:
#                self._lbl.SetLabel(u"")
            ctrlbar = self.GetControlBar(wx.TOP)
            ctrlbar.Layout()

    def OnPageChanged(self, msg):
        """ Notebook tab was changed """
        notebook, pg_num = msg.GetData()
        editor = notebook.GetPage(pg_num)
        self.UpdateForEditor(editor)

    def OnFileLoad(self, msg):
        """Load File message"""
        editor = PyToolsUtils.GetEditorForFile(self._mw, msg.GetData())
        self.UpdateForEditor(editor)

    def OnFileSave(self, msg):
        """Load File message"""
        filename, tmp = msg.GetData()
        editor = PyToolsUtils.GetEditorForFile(self._mw, filename)
        self.UpdateForEditor(editor)
    
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
  
    def OnClear(self, evt):
        self.breakpoints = {}
        self.SaveBreakpoints()
        self.RestoreBreakPoints()
        
