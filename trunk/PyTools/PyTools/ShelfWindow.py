# -*- coding: utf-8 -*-
# Name: ShelfWindow.py
# Purpose: Pylint plugin
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
import copy
import wx

# Editra Libraries
import ed_glob
import util
import eclib
import ed_msg
from profiler import Profile_Get, Profile_Set
from syntax import syntax
import syntax.synglob as synglob

# Local imports
import ToolConfig
from ToolConfig import PYTOOL_CONFIG
from PyToolsUtils import PyToolsUtils
from PythonDirectoryVariables import PythonDirectoryVariables
from PythonSyntaxChecker import PythonSyntaxChecker
from PythonDebugger import PythonDebugger
from CheckResultsList import CheckResultsList
#-----------------------------------------------------------------------------#

_ = wx.GetTranslation
#-----------------------------------------------------------------------------#

ID_COPY_MODULEPATH = wx.NewId()

class FreezeDrawer(object):
    """To be used in 'with' statements. Upon enter freezes the drawing
    and thaws upon exit.

    """
    def __init__(self, wnd):
        self._wnd = wnd

    def __enter__(self):
        self._wnd.Freeze()

    def __exit__(self, eT, eV, tB):
        self._wnd.Thaw()

#-----------------------------------------------------------------------------#

class ShelfWindow(eclib.ControlBox):
    """Syntax Check Results Window"""
    __syntaxCheckers = {
        synglob.ID_LANG_PYTHON: PythonSyntaxChecker
    }

    __debuggers = {
        synglob.ID_LANG_PYTHON: PythonDebugger
    }

    __directoryVariables = {
        synglob.ID_LANG_PYTHON: PythonDirectoryVariables
    }
    def __init__(self, parent):
        """Initialize the window"""
        super(ShelfWindow, self).__init__(parent)

        # Attributes
        # Parent is ed_shelf.EdShelfBook
        self._mw = self.__FindMainWindow()
        self._log = wx.GetApp().GetLog()
        self._listCtrl = CheckResultsList(self,
                                          style=wx.LC_REPORT|wx.BORDER_NONE)
        self._jobtimer = wx.Timer(self)
        self._checker = None
        self._curfile = u""
        self._prevfile = u""
        self._lintrun = False
        self._debugrun = False
        self._localpython = u""
        self._debugargs = u""
        self._config = Profile_Get(PYTOOL_CONFIG, default=dict())

        # Setup
        self._listCtrl.set_mainwindow(self._mw)
        ctrlbar = eclib.ControlBar(self, style=eclib.CTRLBAR_STYLE_GRADIENT)
        ctrlbar.SetVMargin(2, 2)
        if wx.Platform == '__WXGTK__':
            ctrlbar.SetWindowStyle(eclib.CTRLBAR_STYLE_DEFAULT)
        rbmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_PREF), wx.ART_MENU)
        if rbmp.IsNull() or not rbmp.IsOk():
            rbmp = None
        self.cfgbtn = eclib.PlateButton(ctrlbar, wx.ID_ANY, bmp=rbmp,
                                        style=eclib.PB_STYLE_NOBG)
        self.cfgbtn.SetToolTipString(_("Configure"))
        ctrlbar.AddControl(self.cfgbtn, wx.ALIGN_LEFT)
        self._lbl = wx.StaticText(ctrlbar)
        ctrlbar.AddControl(self._lbl)
        ctrlbar.AddStretchSpacer()
        rbmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_BIN_FILE), wx.ART_MENU)
        if rbmp.IsNull() or not rbmp.IsOk():
            rbmp = None
        self.lintbtn = eclib.PlateButton(ctrlbar, wx.ID_ANY, _("Lint"), rbmp,
                                        style=eclib.PB_STYLE_NOBG)
        self.lintbtn.Enable(False)
        ctrlbar.AddControl(self.lintbtn, wx.ALIGN_RIGHT)
        ctrlbar.AddSpacer(20,10)

        self.debugbtn = eclib.PlateButton(ctrlbar, wx.ID_ANY, _("Debug"), rbmp,
                                        style=eclib.PB_STYLE_NOBG)
        self.debugbtn.Enable(False)
        ctrlbar.AddControl(self.debugbtn, wx.ALIGN_RIGHT)
        self.choices = ["1. Local Python", "2. Debug Args", "3. New Debug CmdLine"]
        self.combo = wx.ComboBox(ctrlbar, wx.ID_ANY, value=self.choices[0], choices=self.choices, style=wx.CB_READONLY|eclib.PB_STYLE_NOBG)
        self.combo.Enable(False)
        ctrlbar.AddControl(self.combo, wx.ALIGN_RIGHT)
        self.combocurrent_selection = 0
        self.combotexts = {}
        for i, ignore in enumerate(self.choices):
            self.combotexts[i] = ""
        txtentrysize = wx.Size(512, wx.DefaultSize.GetHeight())
        self.search = wx.SearchCtrl(ctrlbar, wx.ID_ANY, self.combotexts[0], size=txtentrysize, style=eclib.PB_STYLE_NOBG)
        self.search.Enable(False)
        self.search.SetDescriptiveText("")
        self.search.ShowSearchButton(False)
        self.search.ShowCancelButton(True)
        ctrlbar.AddControl(self.search, wx.ALIGN_RIGHT)

        # Layout
        self.SetWindow(self._listCtrl)
        self.SetControlBar(ctrlbar, wx.TOP)

        # Event Handlers
        self.Bind(wx.EVT_TIMER, self.OnJobTimer, self._jobtimer)
        self.Bind(wx.EVT_BUTTON, self.OnShowConfig, self.cfgbtn)
        self.Bind(wx.EVT_BUTTON, self.OnRunLint, self.lintbtn)
        self.Bind(wx.EVT_BUTTON, self.OnRunDebug, self.debugbtn)
        self.Bind(wx.EVT_COMBOBOX, self.OnComboSelect, self.combo)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancelSearch, self.search)

        # Editra Message Handlers
        ed_msg.Subscribe(self.OnFileLoad, ed_msg.EDMSG_FILE_OPENED)
        ed_msg.Subscribe(self.OnFileSave, ed_msg.EDMSG_FILE_SAVED)
        ed_msg.Subscribe(self.OnPageChanged, ed_msg.EDMSG_UI_NB_CHANGED)
        ed_msg.Subscribe(self.OnThemeChanged, ed_msg.EDMSG_THEME_CHANGED)
        ed_msg.Subscribe(self.OnTabMenu, ed_msg.EDMSG_UI_NB_TABMENU)

    def __del__(self):
        self._StopTimer()
        ed_msg.Unsubscribe(self.OnFileLoad)
        ed_msg.Unsubscribe(self.OnFileSave)
        ed_msg.Unsubscribe(self.OnPageChanged)
        ed_msg.Unsubscribe(self.OnThemeChanged)
        ed_msg.Unsubscribe(self.OnTabMenu)

    def GetMainWindow(self):
        return self._mw

    def _StopTimer(self):
        if self._jobtimer.IsRunning():
            self._jobtimer.Stop()

    def __FindMainWindow(self):
        """Find the mainwindow of this control
        @return: MainWindow or None

        """
        def IsMainWin(win):
            """Check if the given window is a main window"""
            return getattr(tlw, '__name__', '') == 'MainWindow'

        tlw = self.GetTopLevelParent()
        if IsMainWin(tlw):
            return tlw
        elif hasattr(tlw, 'GetParent'):
            tlw = tlw.GetParent()
            if IsMainWin(tlw):
                return tlw

        return None

    def _onfileaccess(self, editor):
        # With the text control (ed_stc.EditraStc) this will return the full
        # path of the file or a wx.EmptyString if the buffer does not contain
        # an on disk file
        filename = editor.GetFileName()

        self._listCtrl.set_editor(editor)
        self._listCtrl.DeleteOldRows()

        if not filename:
            return

        filename = os.path.abspath(filename)
        fileext = os.path.splitext(filename)[1]
        if fileext == u"":
            return

        filetype = syntax.GetIdFromExt(fileext[1:]) # pass in file extension
        directoryvariables = self.get_directory_variables(filetype)
        if directoryvariables:
            vardict = directoryvariables.read_dirvarfile(filename)
        else:
            vardict = {}

        self._checksyntax(filetype, vardict, filename)
        self._lintrun = True

    def _launchdebugger(self, editor):
        # With the text control (ed_stc.EditraStc) this will return the full
        # path of the file or a wx.EmptyString if the buffer does not contain
        # an on disk file
        filename = editor.GetFileName()
        self._listCtrl.set_editor(editor)
        self._listCtrl.DeleteOldRows()

        if not filename:
            return

        filename = os.path.abspath(filename)
        fileext = os.path.splitext(filename)[1]
        if fileext == u"":
            return

        filetype = syntax.GetIdFromExt(fileext[1:]) # pass in file extension
        directoryvariables = self.get_directory_variables(filetype)
        if directoryvariables:
            vardict = directoryvariables.read_dirvarfile(filename)
        else:
            vardict = {}

        rows = self._debug(filetype, vardict, filename)
        self._OnListRows(rows)
        self._debugrun = True

    def UpdateForEditor(self, editor, force=False):
        langid = getattr(editor, 'GetLangId', lambda: -1)()
        ispython = langid == synglob.ID_LANG_PYTHON
        self.lintbtn.Enable(ispython)
        self.debugbtn.Enable(ispython)
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
            key = "PYTHON_%s" % self._prevfile
            if emptycombotexts:
                if key in self._config:
                    del self._config["PYTHON_%s" % self._prevfile]
            else:
                pythoninfo = (self.combocurrent_selection, self.combotexts)
                self._config[key] = copy.deepcopy(pythoninfo)
                Profile_Set(PYTOOL_CONFIG, self._config)

        filename = editor.GetFileName()
        self._prevfile = filename
        pythoninfo = self._config.get("PYTHON_%s" % filename, None)
        if pythoninfo:
            self.combocurrent_selection, self.combotexts = pythoninfo
            self.combo.SetSelection(self.combocurrent_selection)
            self.search.SetValue(self.combotexts[self.combocurrent_selection])
        else:
            self.combocurrent_selection = 0
            self.combotexts = {}
            for i, ignore in enumerate(self.choices):
                self.combotexts[i] = ""
            self.combo.SetSelection(0)
            self.search.SetValue("")

        if force or (not self._lintrun and not self._debugrun):
            ctrlbar = self.GetControlBar(wx.TOP)
            ctrlbar.Layout()

    def OnPageChanged(self, msg):
        """ Notebook tab was changed """
        notebook, pg_num = msg.GetData()
        editor = notebook.GetPage(pg_num)
        if ToolConfig.GetConfigValue(ToolConfig.TLC_AUTO_RUN):
            wx.CallAfter(self._onfileaccess, editor)
            self.UpdateForEditor(editor, True)
        else:
            self.UpdateForEditor(editor)

    def OnFileLoad(self, msg):
        """Load File message"""
        editor = self._GetEditorForFile(msg.GetData())
        if ToolConfig.GetConfigValue(ToolConfig.TLC_AUTO_RUN):
            wx.CallAfter(self._onfileaccess, editor)
            self.UpdateForEditor(editor, True)
        else:
            self.UpdateForEditor(editor)

    def OnFileSave(self, msg):
        """Load File message"""
        filename, tmp = msg.GetData()
        editor = self._GetEditorForFile(filename)
        if ToolConfig.GetConfigValue(ToolConfig.TLC_AUTO_RUN):
            wx.CallAfter(self._onfileaccess, editor)
            self.UpdateForEditor(editor, True)
        else:
            self.UpdateForEditor(editor)

    def OnThemeChanged(self, msg):
        """Icon theme has changed so update button"""
        rbmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_BIN_FILE), wx.ART_MENU)
        if rbmp.IsNull() or not rbmp.IsOk():
            return
        else:
            self.lintbtn.SetBitmap(rbmp)
            self.lintbtn.Refresh()
            self.debugbtn.SetBitmap(rbmp)
            self.debugbtn.Refresh()

    def OnShowConfig(self, event):
        """Show the configuration dialog"""
        mw = self.GetMainWindow()
        dlg = ToolConfig.ToolConfigDialog(mw)
        dlg.CenterOnParent()
        dlg.ShowModal()

    def OnRunLint(self, event):
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            wx.CallAfter(self._onfileaccess, editor)

    def OnRunDebug(self, event):
        self.combotexts[self.combocurrent_selection] = self.search.GetValue()
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            wx.CallAfter(self._launchdebugger, editor)

    def OnCancelSearch(self, event):
        self.combotexts[self.combocurrent_selection] = ""
        self.search.SetValue("")

    def OnComboSelect(self, event):
        """Handle change of combo choice"""
        self.combotexts[self.combocurrent_selection] = self.search.GetValue()
        self.combocurrent_selection = self.combo.GetSelection()
        self.search.SetValue(self.combotexts[self.combocurrent_selection])
        editor = wx.GetApp().GetCurrentBuffer()
        self.UpdateForEditor(editor, True)

    def OnTabMenu(self, msg):
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            langid = getattr(editor, 'GetLangId', lambda: -1)()
            ispython = langid == synglob.ID_LANG_PYTHON
            if ispython:
                contextmenumanager = msg.GetData()
                menu = contextmenumanager.GetMenu()
                menu.Append(ID_COPY_MODULEPATH, _("Copy Module Path"))
                contextmenumanager.AddHandler(ID_COPY_MODULEPATH, self.copy_module_path)

    def copy_module_path(self, editor, evt):
        path = editor.GetFileName()
        if path is not None:
            childPath, _ = PyToolsUtils.get_packageroot(path)
            modulepath = PyToolsUtils.get_modulepath(childPath)
            util.SetClipboardText(modulepath)

    def get_syntax_checker(self, filetype, vardict, filename):
        try:
            return self.__syntaxCheckers[filetype](vardict, filename)
        except Exception:
            pass
        return None

    def get_debugger(self, filetype, vardict, filename):
        try:
            return self.__debuggers[filetype](vardict, filename)
        except Exception:
            pass
        return None

    def get_directory_variables(self, filetype):
        try:
            return self.__directoryVariables[filetype]()
        except Exception:
            pass
        return None

    def _checksyntax(self, filetype, vardict, filename):
        syntaxchecker = self.get_syntax_checker(filetype, vardict, filename)
        if not syntaxchecker:
            return
        self._checker = syntaxchecker
        self._curfile = filename

        # Start job timer
        self._StopTimer()
        self._jobtimer.Start(250, True)

    def _debug(self, filetype, vardict, filename):
        debugger = self.get_debugger(filetype, vardict, filename)
        if not debugger:
            return []
        debugargs = self.combotexts[0]
        debuggerargs = self.combotexts[1]
        return debugger.Debug(debuggerargs, debugargs)

    def _OnListRows(self, data):
        # Data is something like
        # [('Syntax Error', '__all__ = ["CSVSMonitorThread"]', 7)]
        if len(data) != 0:
            self._listCtrl.PopulateRows(data)
            self._listCtrl.RefreshRows()
        mwid = self.GetMainWindow().GetId()
        ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (mwid, False))

    def OnJobTimer(self, evt):
        """Start a syntax check job"""
        if self._checker:
            util.Log("[PyLint][info] fileName %s" % (self._curfile))
            mwid = self.GetMainWindow().GetId()
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (mwid, True))
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_STATE, (mwid, -1, -1))
            # Update the label to show what file the results are for
            self._lbl.SetLabel(os.path.basename(self._curfile))
            self._checker.Check(self._OnListRows)

    def delete_rows(self):
        self._listCtrl.DeleteOldRows()

    def _GetEditorForFile(self, fname):
        """Return the EdEditorView that's managing the file, if available
        @param fname: File name to open
        @param mainw: MainWindow instance to open the file in
        @return: Text control managing the file
        @rtype: ed_editv.EdEditorView

        """
        nb = self._mw.GetNotebook()
        for page in nb.GetTextControls():
            if page.GetFileName() == fname:
                return nb.GetPage(page.GetTabIndex())

        return None
