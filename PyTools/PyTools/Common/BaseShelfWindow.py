# -*- coding: utf-8 -*-
# Name: BaseShelfWindow.py
# Purpose: Base shelf window
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Base Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx

# Editra Libraries
import ed_glob
import eclib
import ed_basewin
import ed_msg
from profiler import Profile_Get, Profile_Set
import syntax.synglob as synglob

# Local imports
from PyTools.Common.ToolConfig import ToolConfigDialog
from PyTools.Common.PythonDirectoryVariables import PythonDirectoryVariables

# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class BaseShelfWindow(ed_basewin.EdBaseCtrlBox):
    __directoryVariables = {
        synglob.ID_LANG_PYTHON: PythonDirectoryVariables
    }

    def __init__(self, parent):
        """Initialize the window"""
        super(BaseShelfWindow, self).__init__(parent)

        # Attributes
        # Parent is ed_shelf.EdShelfBook
        self._mw = ed_basewin.FindMainWindow(self)
        self._log = wx.GetApp().GetLog()
        self.taskbtn = None
        self._listCtrl = None
        self._imglst = list()
        
        def do_nothing():
            pass
        self.destroyfn = do_nothing
            
    def setup(self, listCtrl, *args):
        self._listCtrl = listCtrl
        self._curfile = u""
        self._hasrun = False
        self._jobtimer = wx.Timer(self)

        # Setup
        if len(args) == 0:
            self._listCtrl.set_mainwindow(self._mw)            
        else:
            for ctrl in args:
                ctrl.set_mainwindow(self._mw)            
                
        self.ctrlbar = self.CreateControlBar(wx.TOP)
        self.cfgbtn = self.AddPlateButton(u"", ed_glob.ID_PREF, wx.ALIGN_LEFT)
        self.cfgbtn.SetToolTipString(_("Configure"))
        return self.ctrlbar

    def layout(self, taskbtndesc=None, taskfn=None, timerfn=None):
        if taskfn:
            rbmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_BIN_FILE), wx.ART_MENU)
            if rbmp.IsNull() or not rbmp.IsOk():
                rbmp = None
            self.taskbtn = eclib.PlateButton(self.ctrlbar, wx.ID_ANY, _(taskbtndesc), rbmp,
                                            style=eclib.PB_STYLE_NOBG)
            self.ctrlbar.AddControl(self.taskbtn, wx.ALIGN_RIGHT)
            self.Bind(wx.EVT_BUTTON, taskfn, self.taskbtn)

        # Layout
        self.SetWindow(self._listCtrl)
        self.SetControlBar(self.ctrlbar, wx.TOP)

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnShowConfig, self.cfgbtn)
        if timerfn:
            self.Bind(wx.EVT_TIMER, timerfn, self._jobtimer)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy, self)

        # Editra Message Handlers
        ed_msg.Subscribe(self.OnThemeChanged, ed_msg.EDMSG_THEME_CHANGED)

    def GetMainWindow(self):
        return self._mw

    # Overridden by derived classes
    def Unsubscription(self):
        pass
    
    def OnDestroy(self, evt):
        """Stop timer and disconnect message handlers"""
        self._StopTimer()
        ed_msg.Unsubscribe(self.OnThemeChanged)
        self.Unsubscription()

    def _StopTimer(self):
        if self._jobtimer.IsRunning():
            self._jobtimer.Stop()

    def OnThemeChanged(self, msg):
        """Icon theme has changed so update button"""
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_PREF), wx.ART_MENU)
        self.cfgbtn.SetBitmap(bmp)
        self.cfgbtn.Refresh()

    def OnShowConfig(self, event):
        """Show the configuration dialog"""
        dlg = ToolConfigDialog(self._mw)
        dlg.CenterOnParent()
        dlg.ShowModal()

    def get_directory_variables(self, filetype):
        try:
            return self.__directoryVariables[filetype]()
        except Exception:
            pass
        return None

    def Clear(self):
        self._listCtrl.Clear()
        