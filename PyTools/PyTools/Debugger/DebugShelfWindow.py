# -*- coding: utf-8 -*-
# Name: DebugShelfWindow.py
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
from time import sleep
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
from PyTools.Common import ToolConfig
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.Debugger.DebugMessageHandler import DebugMessageHandler
from PyTools.Common import Images
from PyTools.Debugger.DebuggeeWindow import DebuggeeWindow
from PyTools.Debugger.PythonDebugger import PythonDebugger
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation
#-----------------------------------------------------------------------------#

class DebugShelfWindow(BaseShelfWindow, DebugMessageHandler):
    """Module Debug Results Window"""
    __debuggers = {
        synglob.ID_LANG_PYTHON: PythonDebugger
    }

    def __init__(self, parent):
        """Initialize the window"""
        BaseShelfWindow.__init__(self, parent)
        DebugMessageHandler.__init__(self)

        # Attributes
        ctrlbar = self.setup(DebuggeeWindow(self))
        ctrlbar.AddControl(wx.StaticLine(ctrlbar, size=(-1, 16), style=wx.SL_VERTICAL),
                           wx.ALIGN_LEFT)
        self.gobtn = self.AddPlateButton(u"", Images.Go.Bitmap, wx.ALIGN_LEFT)
        self.gobtn.ToolTip = wx.ToolTip(_("Run to next breakpoint"))
        self.abortbtn = self.AddPlateButton(u"", Images.Stop.Bitmap, wx.ALIGN_LEFT)
        self.abortbtn.ToolTip = wx.ToolTip(_("Stop debugging"))
        ctrlbar.AddControl(wx.StaticLine(ctrlbar, size=(-1, 16), style=wx.SL_VERTICAL),
                           wx.ALIGN_LEFT)
        self.stepinbtn = self.AddPlateButton(u"", Images.StepIn.Bitmap, wx.ALIGN_LEFT)
        self.stepinbtn.ToolTip = wx.ToolTip(_("Step In"))
        self.stepovbtn = self.AddPlateButton(u"", Images.StepOver.Bitmap, wx.ALIGN_LEFT)
        self.stepovbtn.ToolTip = wx.ToolTip(_("Step Over"))
        self.stepoutbtn = self.AddPlateButton(u"", Images.StepOut.Bitmap, wx.ALIGN_LEFT)
        self.stepoutbtn.ToolTip = wx.ToolTip(_("Step Out"))
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
        RPDBDEBUGGER.mainwindow = self._mw

        # Attributes
        self._debugger = None
        self._debugrun = False
        self._debugargs = ""

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnGo, self.gobtn)
        self.Bind(wx.EVT_BUTTON, self.OnAbort, self.abortbtn)
        self.Bind(wx.EVT_BUTTON, self.OnStepIn, self.stepinbtn)
        self.Bind(wx.EVT_BUTTON, self.OnStepOver, self.stepovbtn)
        self.Bind(wx.EVT_BUTTON, self.OnStepOut, self.stepoutbtn)
        self.Bind(wx.EVT_COMBOBOX, self.OnComboSelect, self.combo)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancelSearch, self.search)

    def Unsubscription(self):
        if RPDBDEBUGGER.attached:
            RPDBDEBUGGER.do_detach()
        DebugMessageHandler.Unsubscription(self)

    def OnGo(self, event):
        RPDBDEBUGGER.do_go()

    def OnAbort(self, event):
        RPDBDEBUGGER.abort()

    def OnStepIn(self, event):
        RPDBDEBUGGER.do_step()

    def OnStepOver(self, event):
        RPDBDEBUGGER.do_next()

    def OnStepOut(self, event):
        pass #TODO: Add Step Out

    def OnCancelSearch(self, event):
        self.combotexts[self.combocurrent_selection] = ""
        self.search.SetValue("")

    def OnComboSelect(self, event):
        """Handle change of combo choice"""
        self.combotexts[self.combocurrent_selection] = self.search.GetValue()
        self.combocurrent_selection = self.combo.GetSelection()
        self.search.SetValue(self.combotexts[self.combocurrent_selection])

    def OnEditorUpdate(self, ispython, filename, force):
        self.taskbtn.Enable(ispython)
        self.combo.Enable(ispython)
        self.search.Enable(ispython)
        self.combotexts[self.combocurrent_selection] = self.search.GetValue()
        config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        if self._prevfile:
            emptycombotexts = True
            for key in self.combotexts:
                combotext = self.combotexts[key]
                if combotext:
                    emptycombotexts = False
                    break
            key = "DEBUG_%s" % self._prevfile
            if emptycombotexts:
                if key in config:
                    del config["DEBUG_%s" % self._prevfile]
            else:
                debuginfo = (self.combocurrent_selection, self.combotexts)
                config[key] = copy.deepcopy(debuginfo)
                Profile_Set(ToolConfig.PYTOOL_CONFIG, config)

        debuginfo = config.get("DEBUG_%s" % filename, None)
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
            ctrlbar = self.GetControlBar(wx.TOP)
            ctrlbar.Layout()

    def _ondebug(self, editor):
        # With the text control (ed_stc.EditraStc) this will return the full
        # path of the file or a wx.EmptyString if the buffer does not contain
        # an on disk file
        filename = os.path.normcase(editor.GetFileName())
        self._listCtrl.Clear()

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
        self._debug(filetype, vardict, filename)
        self._hasrun = True

    def OnDebug(self, event):
        self.combotexts[self.combocurrent_selection] = self.search.GetValue()
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            wx.CallAfter(self._ondebug, editor)

    def get_debugger(self, filetype, vardict, filename):
        try:
            programargs = self.combotexts[0]
            debuggerargs = self.combotexts[1]
            return self.__debuggers[filetype](vardict, debuggerargs, 
                programargs, filename, self._listCtrl)
        except Exception:
            pass
        return None
        
    def restorepylint_autorun(self):
        config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        config[ToolConfig.TLC_LINT_AUTORUN] = True
        Profile_Set(ToolConfig.PYTOOL_CONFIG, config)
        self._listCtrl.AddText("Reenabling Pylint Autorun.")
    
    def _debug(self, filetype, vardict, filename):
        debugger = self.get_debugger(filetype, vardict, filename)
        if not debugger:
            return []
        self._debugger = debugger
        self._curfile = filename

        config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        mode = config.get(ToolConfig.TLC_LINT_AUTORUN, False)
        if mode:
            config[ToolConfig.TLC_LINT_AUTORUN] = False
            Profile_Set(ToolConfig.PYTOOL_CONFIG, config)
            self._listCtrl.AddText("Disabling Pylint Autorun during Debug.")
            self._listCtrl.restoreautorun = self.restorepylint_autorun
        else:
            self._listCtrl.restoreautorun = lambda:None

        # Start job timer
        self._StopTimer()
        self._jobtimer.Start(250, True)

    def OnJobTimer(self, evt):
        """Start a debug job"""
        if self._debugger:
            util.Log("[PyDebug][info] fileName %s" % (self._curfile))
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (self._mw.GetId(), True))
            self._debugger.Debug()
