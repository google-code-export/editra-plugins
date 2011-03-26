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
import util
import eclib
import ed_msg
from profiler import Profile_Get, Profile_Set
from syntax import syntax
import syntax.synglob as synglob

# Local imports
from PyTools.Common import ToolConfig
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.Common import Images
from PyTools.Debugger.DebuggeeWindow import DebuggeeWindow
from PyTools.Debugger.PythonDebugger import PythonDebugger
from PyTools.Debugger import RPDBDEBUGGER
from PyTools.Debugger import MESSAGEHANDLER

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

        # Attributes
        ctrlbar = self.setup(DebuggeeWindow(self))
        ctrlbar.AddControl(wx.StaticLine(ctrlbar, size=(-1, 16), style=wx.SL_VERTICAL),
                           wx.ALIGN_LEFT)
        self.gobtn = self.AddPlateButton(u"", Images.Go.Bitmap, wx.ALIGN_LEFT)
        self.gobtn.ToolTip = wx.ToolTip(_("Run"))
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
        self.breakbtn = self.AddPlateButton(u"", Images.Break.Bitmap, wx.ALIGN_LEFT)
        self.breakbtn.ToolTip = wx.ToolTip(_("Break"))
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

        self.layout(None, None, self.OnJobTimer)

        # Attributes
        RPDBDEBUGGER.mainwindow = self._mw
        RPDBDEBUGGER.debugbuttonsupdate = self.OnButtonsUpdate
        RPDBDEBUGGER.disabledebugbuttons = self.DisableButtons
#        MESSAGEHANDLER.mainwindow = self._mw # TODO:
        MESSAGEHANDLER.debugeditorupdate = self.OnEditorUpdate
        self._debugger = None
        self._debugrun = False
        self._debugargs = ""

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnGo, self.gobtn)
        self.Bind(wx.EVT_BUTTON, self.OnAbort, self.abortbtn)
        self.Bind(wx.EVT_BUTTON, self.OnStepIn, self.stepinbtn)
        self.Bind(wx.EVT_BUTTON, self.OnStepOver, self.stepovbtn)
        self.Bind(wx.EVT_BUTTON, self.OnStepOut, self.stepoutbtn)
        self.Bind(wx.EVT_BUTTON, self.OnBreak, self.breakbtn)
        self.Bind(wx.EVT_COMBOBOX, self.OnComboSelect, self.combo)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancelSearch, self.search)

    def Unsubscription(self):
        if RPDBDEBUGGER.attached:
            RPDBDEBUGGER.do_detach()
        RPDBDEBUGGER.debugbuttonsupdate = lambda:None
        RPDBDEBUGGER.disabledebugbuttons = lambda:None
        MESSAGEHANDLER.debugeditorupdate = lambda x,y,z:None

    def OnCancelSearch(self, event):
        self.combotexts[self.combocurrent_selection] = ""
        self.search.SetValue("")

    def OnComboSelect(self, event):
        """Handle change of combo choice"""
        self.combotexts[self.combocurrent_selection] = self.search.GetValue()
        self.combocurrent_selection = self.combo.GetSelection()
        self.search.SetValue(self.combotexts[self.combocurrent_selection])

    def DisableButtons(self):
        self.gobtn.Enable(False)
        self.abortbtn.Enable(False)
        self.stepinbtn.Enable(False)
        self.stepovbtn.Enable(False)
        self.stepoutbtn.Enable(False)
        self.breakbtn.Enable(False)
        self.combo.Enable(False)
        self.search.Enable(False)
    
    def _onbuttonsupdate(self, ispython):
        attached = RPDBDEBUGGER.attached
        broken = RPDBDEBUGGER.broken
        attachedandbroken = attached and broken
        ispythonandnotattached = ispython and not attached
        self.gobtn.Enable(attachedandbroken or ispythonandnotattached)
        self.abortbtn.Enable(attached)
        self.stepinbtn.Enable(attachedandbroken)
        self.stepovbtn.Enable(attachedandbroken)
        self.stepoutbtn.Enable(attachedandbroken)
        self.breakbtn.Enable(attached and not broken and not RPDBDEBUGGER.analyzing)
        self.combo.Enable(ispythonandnotattached)
        self.search.Enable(ispythonandnotattached)

    def OnButtonsUpdate(self):
        editor = wx.GetApp().GetCurrentBuffer()
        if not editor:
            self._onbuttonsupdate(False)
            return
        langid = getattr(editor, 'GetLangId', lambda: -1)()
        ispython = langid == synglob.ID_LANG_PYTHON
        self._onbuttonsupdate(ispython)
        
    def OnEditorUpdate(self, ispython, filename, force):
        self._onbuttonsupdate(ispython)
        self.combotexts[self.combocurrent_selection] = self.search.GetValue()
        config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        if MESSAGEHANDLER._prevfile:
            emptycombotexts = True
            for key in self.combotexts:
                combotext = self.combotexts[key]
                if combotext:
                    emptycombotexts = False
                    break
            key = "DEBUG_%s" % MESSAGEHANDLER._prevfile
            if emptycombotexts:
                if key in config:
                    del config["DEBUG_%s" % MESSAGEHANDLER._prevfile]
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

    def OnGo(self, event):
        if RPDBDEBUGGER.attached:
            RPDBDEBUGGER.do_go()
            return
            
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
        trap = config.get(ToolConfig.TLC_TRAP_EXCEPTIONS, True)
        RPDBDEBUGGER.set_trap_unhandled_exceptions(trap)
        synchronicity = config.get(ToolConfig.TLC_SYNCHRONICITY, True)
        RPDBDEBUGGER.set_synchronicity(synchronicity)
        autofork = config.get(ToolConfig.TLC_AUTO_FORK, True)
        forkmode = config.get(ToolConfig.TLC_FORK_MODE, False)
        RPDBDEBUGGER.set_fork_mode(forkmode, autofork)
        encoding = config.get(ToolConfig.TLC_EXECEVALENCODING, "auto")
        escaping = config.get(ToolConfig.TLC_EXECEVALESCAPING, True)
        RPDBDEBUGGER.set_encoding(encoding, escaping)
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
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_STATE, (self._mw.GetId(), -1, -1))
            self.DisableButtons()
            self._debugger.Debug()

    def OnAbort(self, event):
        RPDBDEBUGGER.do_abort()

    def OnStepIn(self, event):
        RPDBDEBUGGER.do_step()

    def OnStepOver(self, event):
        RPDBDEBUGGER.do_next()

    def OnStepOut(self, event):
        RPDBDEBUGGER.do_return()

    def OnBreak(self, event):
        RPDBDEBUGGER.do_break()