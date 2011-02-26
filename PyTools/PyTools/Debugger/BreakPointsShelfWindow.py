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
        ctrlbar = self.setup(BreakPointsList(self, style=wx.LC_REPORT|wx.BORDER_NONE))
        ctrlbar.AddStretchSpacer()
        txtentrysize = wx.Size(256, wx.DefaultSize.GetHeight())
        self.textentry = eclib.CommandEntryBase(ctrlbar, wx.ID_ANY, size=txtentrysize,
                                           style=wx.TE_PROCESS_ENTER|wx.WANTS_CHARS)
        ctrlbar.AddControl(self.textentry, wx.ALIGN_RIGHT)
        self.layout("Go", self.OnGo)

        # Attributes
        self._config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())

        # Editra Message Handlers
        ed_msg.Subscribe(self.OnFileLoad, ed_msg.EDMSG_FILE_OPENED)
        ed_msg.Subscribe(self.OnFileSave, ed_msg.EDMSG_FILE_SAVED)
        ed_msg.Subscribe(self.OnPageChanged, ed_msg.EDMSG_UI_NB_CHANGED)
        ed_msg.Subscribe(self.OnContextMenu, ed_msg.EDMSG_UI_STC_CONTEXT_MENU)
        
        self.breakpoints = self._config.get(ToolConfig.TLC_BREAKPOINTS, dict())
        RPDBDEBUGGER.breakpointmanager.set_bpshelfwindow(self)

    def GetBreakPoints(self):
        return self.breakpoints

    def Destroy(self):
        ed_msg.Unsubscribe(self.OnFileLoad)
        ed_msg.Unsubscribe(self.OnFileSave)
        ed_msg.Unsubscribe(self.OnPageChanged)
        ed_msg.Unsubscribe(self.OnContextMenu)

    def UpdateForEditor(self, editor, force=False):
        langid = getattr(editor, 'GetLangId', lambda: -1)()
        ispython = langid == synglob.ID_LANG_PYTHON
        self.taskbtn.Enable(ispython)

        filename = editor.GetFileName()

        self._config[ToolConfig.TLC_BREAKPOINTS] = copy.deepcopy(self.breakpoints)
        Profile_Set(ToolConfig.PYTOOL_CONFIG, self._config)
        self._listCtrl.PopulateRows(self.breakpoints)
            
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

    def OnGo(self, event):
        RPDBDEBUGGER.do_go()
    
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
        filepath = editor.GetFileName()
        lineno = editor.GetCurrentLineNum()
        if not filepath or not lineno:
            return
        if filepath in self.breakpoints:
            linenos = self.breakpoints[filepath]
            if lineno in linenos:
                editor.DeleteBreakpoint(lineno)
                enabled, exprstr, bpid = linenos[lineno]
                RPDBDEBUGGER.delete_breakpoint(bpid)
                del linenos[lineno]
                return
        else:
            linenos = {}
            self.breakpoints[filepath] = linenos
        editor.SetBreakpoint(lineno)
        bp = RPDBDEBUGGER.set_breakpoint(filepath, lineno)
        bpid = None
        if bp:
            bpid = bp.m_id
        linenos[lineno] = (True, "", bpid)
