# -*- coding: utf-8 -*-
# Name: DebugShelfWindow.py
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
from PyTools.Debugger.DebugResultsList import DebugResultsList
from PyTools.Debugger.PythonDebugger import PythonDebugger

# Globals
_ = wx.GetTranslation
#-----------------------------------------------------------------------------#

class DebugShelfWindow(BaseShelfWindow):
    """Module Debug Results Window"""
    __debuggers = {
        synglob.ID_LANG_PYTHON: PythonDebugger
    }

    def __init__(self, parent):
        """Initialize the window"""
        super(DebugShelfWindow, self).__init__(parent)
        ctrlbar = self.setup(DebugResultsList(self, style=wx.LC_REPORT|wx.BORDER_NONE))
        ctrlbar.AddStretchSpacer()
        self.choices = ["Program Args", "Debugger Args"]
        self.combo = wx.ComboBox(ctrlbar, wx.ID_ANY, value=self.choices[0], choices=self.choices, style=wx.CB_READONLY|eclib.PB_STYLE_NOBG)
        self.combo.Enable(False)
        ctrlbar.AddControl(self.combo, wx.ALIGN_RIGHT)
        self.combocurrent_selection = 0
        self.combotexts = {}
        for i, ignore in enumerate(self.choices):
            self.combotexts[i] = ""
        txtentrysize = wx.Size(512, wx.DefaultSize.GetHeight())
        self.search = eclib.CommandEntryBase(ctrlbar, wx.ID_ANY, size=txtentrysize,
                                           style=wx.TE_PROCESS_ENTER|wx.WANTS_CHARS|eclib.PB_STYLE_NOBG)
        self.search.Enable(False)
        self.search.SetDescriptiveText("")
        self.search.ShowSearchButton(False)
        self.search.ShowCancelButton(True)
        ctrlbar.AddControl(self.search, wx.ALIGN_RIGHT)

        self.layout("Debug", self.OnDebug, self.OnJobTimer)

        # Attributes
        self._debugger = None
        self._prevfile = u""
        self._debugrun = False
        self._debugargs = ""
        self._config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())

        # Event Handlers
        self.Bind(wx.EVT_COMBOBOX, self.OnComboSelect, self.combo)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancelSearch, self.search)

        # Editra Message Handlers
        ed_msg.Subscribe(self.OnFileLoad, ed_msg.EDMSG_FILE_OPENED)
        ed_msg.Subscribe(self.OnFileSave, ed_msg.EDMSG_FILE_SAVED)
        ed_msg.Subscribe(self.OnPageChanged, ed_msg.EDMSG_UI_NB_CHANGED)

    def OnCancelSearch(self, event):
        self.combotexts[self.combocurrent_selection] = ""
        self.search.SetValue("")

    def OnComboSelect(self, event):
        """Handle change of combo choice"""
        self.combotexts[self.combocurrent_selection] = self.search.GetValue()
        self.combocurrent_selection = self.combo.GetSelection()
        self.search.SetValue(self.combotexts[self.combocurrent_selection])

    def UpdateForEditor(self, editor, force=False):
        langid = getattr(editor, 'GetLangId', lambda: -1)()
        ispython = langid == synglob.ID_LANG_PYTHON
        self.taskbtn.Enable(ispython)
        self.combo.Enable(ispython)
        self.search.Enable(ispython)
        self.combotexts[self.combocurrent_selection] = self.search.GetValue()
        if self._prevfile:
            emptycombotexts = True
            for key in self.combotexts:
                combotext = self.combotexts[key]
                if combotext:
                    emptycombotexts = False
                    break
            key = "DEBUG_%s" % self._prevfile
            if emptycombotexts:
                if key in self._config:
                    del self._config["DEBUG_%s" % self._prevfile]
            else:
                debuginfo = (self.combocurrent_selection, self.combotexts)
                self._config[key] = copy.deepcopy(debuginfo)
                Profile_Set(ToolConfig.PYTOOL_CONFIG, self._config)

        filename = editor.GetFileName()
        self._prevfile = filename
        debuginfo = self._config.get("DEBUG_%s" % filename, None)
        if debuginfo:
            self.combocurrent_selection, self.combotexts = debuginfo
            self.combo.SetSelection(self.combocurrent_selection)
            self.search.SetValue(self.combotexts[self.combocurrent_selection])
        else:
            self.combocurrent_selection = 0
            self.combotexts = {}
            for i, ignore in enumerate(self.choices):
                self.combotexts[i] = ""
            self.combo.SetSelection(0)
            self.search.SetValue("")

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

    def _ondebug(self, editor, moduletofind):
        # With the text control (ed_stc.EditraStc) this will return the full
        # path of the file or a wx.EmptyString if the buffer does not contain
        # an on disk file
        filename = editor.GetFileName()
        self._listCtrl.DeleteOldRows()

        vardict = {}
        if filename:
            filename = os.path.abspath(filename)
            fileext = os.path.splitext(filename)[1]
            if fileext:
                filetype = syntax.GetIdFromExt(fileext[1:]) # pass in file extension
                directoryvariables = self.get_directory_variables(filetype)
                if directoryvariables:
                    vardict = directoryvariables.read_dirvarfile(filename)

        self._debug(synglob.ID_LANG_PYTHON, vardict, moduletofind)
        self._hasrun = True

    def OnDebug(self, event):
        self.combotexts[self.combocurrent_selection] = self.search.GetValue()
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            wx.CallAfter(self._ondebug, editor)

    def get_debugger(self, filetype, vardict, debuggerargs, programargs, filename):
        try:
            return self.__debuggers[filetype](vardict, debuggerargs, programargs, filename)
        except Exception:
            pass
        return None

    def _debug(self, filetype, vardict, filename):
        programargs = self.combotexts[0]
        debuggerargs = self.combotexts[1]
        debugger = self.get_debugger(filetype, vardict, debuggerargs, programargs, filename)
        if not debugger:
            return []
        self._debugger = debugger
        self._curfile = filename

        # Start job timer
        self._StopTimer()
        self._jobtimer.Start(250, True)

    def _OnDebugData(self, data):
        # Data is something like
        # [('Debug Error', '__all__ = ["CSVSMonitorThread"]', 7)]
        if len(data) != 0:
            self._listCtrl.PopulateRows(data)
            self._listCtrl.RefreshRows()
        mwid = self.GetMainWindow().GetId()
        ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (mwid, False))

    def OnJobTimer(self, evt):
        """Start a debug job"""
        if self._debugger:
            util.Log("[PyDebug][info] fileName %s" % (self._curfile))
            mwid = self.GetMainWindow().GetId()
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (mwid, True))
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_STATE, (mwid, -1, -1))
            self._debugger.Debug(self._OnDebugData)

    def delete_rows(self):
        self._listCtrl.DeleteOldRows()




