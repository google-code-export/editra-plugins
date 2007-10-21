# -*- coding: utf-8 -*-
"""Adds a Projects sidepanel"""
__author__ = "Kevin D. Smith"
__version__ = "0.1"

import wx 
import stat
import os 
import time
import fnmatch
import threading
import plugin 
import string
import ed_glob
import iface
import ed_menu
from profiler import Profile_Get, Profile_Set
from ProjectPane import ProjectPane

_ = wx.GetTranslation
PANE_NAME = ProjectPane.PANE_NAME

class Logger(object):
    def WriteText(self, *args):
        pass

class Projects(plugin.Plugin):
    """Adds a projects pane to the view menu"""
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        """Adds the view menu entry and registers the event handler"""
        mw = parent
        self._log = wx.GetApp().GetLog()
        if mw != None:
            self._log("[projects] Installing projects plugin")

            self._projects = ProjectPane(mw)
            mw._mgr.AddPane(self._projects, wx.aui.AuiPaneInfo().Name(PANE_NAME).\
                            Caption("Projects").Left().Layer(1).\
                            CloseButton(True).MaximizeButton(False).\
                            BestSize(wx.Size(215, 350)))

            # Get settings from profile
            if Profile_Get('Projects.Show', 'bool', False):
                mw._mgr.GetPane(PANE_NAME).Show()
            else:
                mw._mgr.GetPane(PANE_NAME).Hide()

            mw._mgr.Update()

            # Event Handlers
            mw.Bind(wx.aui.EVT_AUI_PANE_CLOSE, self.OnPaneClose)

    def GetMenuHandlers(self):
        return [(self._projects.ID_PROJECTS, self._projects.OnShowProjects)]

    def GetUIHandlers(self):
        return list()

    def OnPaneClose(self, evt):
        """ Handles when the pane is closed to update the profile """
        pane = evt.GetPane()
        if pane.name == PANE_NAME:
            Profile_Set('Projects.Show', False)
        else:
            evt.Skip()
