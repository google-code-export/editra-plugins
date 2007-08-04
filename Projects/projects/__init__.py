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
import ed_main
import ed_menu
from profiler import Profile_Get, Profile_Set
from ProjectPane import ProjectPane

PANE_NAME = u'Projects'
ID_PROJECTS = wx.NewId()
_ = wx.GetTranslation

class Logger(object):
    def WriteText(self, *args):
        pass

class Projects(plugin.Plugin):
    """Adds a projects pane to the view menu"""
    plugin.Implements(ed_main.MainWindowI)
    def PlugIt(self, parent):
        """Adds the view menu entry and registers the event handler"""
        mw = parent
        self._log = wx.GetApp().GetLog()
        if mw != None:
            self._log("[projects] Installing projects plugin")
            
            mb = mw.GetMenuBar()
            vm = mb.GetMenuByName("view")
            self._mi = vm.InsertAlpha(ID_PROJECTS, _("Projects"), 
                                      _("Open Projects sidepanel"),
                                      wx.ITEM_CHECK,
                                      after=ed_glob.ID_PRE_MARK)

            self._projects = ProjectPane(mw)

            mw._mgr.AddPane(self._projects, wx.aui.AuiPaneInfo().Name(PANE_NAME).\
                            Caption("Projects").Left().Layer(1).\
                            CloseButton(True).MaximizeButton(False).\
                            BestSize(wx.Size(215, 350)))

            # Get settings from profile
            if Profile_Get('Projects.Show', 'bool', False):
                mw._mgr.GetPane(PANE_NAME).Show()
                self._mi.Check(True)
            else:
                mw._mgr.GetPane(PANE_NAME).Hide()
                self._mi.Check(False)

            mw._mgr.Update()

            # Event Handlers
            mw.Bind(wx.EVT_MENU, self.OnShowProjects, id=ID_PROJECTS)
            mw.Bind(wx.aui.EVT_AUI_PANE_CLOSE, self.OnPaneClose)


    def OnPaneClose(self, evt):
        """ Handles when the pane is closed to update the profile """
        pane = evt.GetPane()
        if pane.name == PANE_NAME:
            Profile_Set('Projects.Show', False)
            self._mi.Check(False)
        else:
            evt.Skip()

    def OnShowProjects(self, evt):
        """ Shows the projects """
        if evt.GetId() == ID_PROJECTS:
            mw = wx.GetApp().GetMainWindow().GetFrameManager()
            pane = mw.GetPane(PANE_NAME).Hide()
            if Profile_Get('Projects.Show', 'bool', False) and pane.IsShown():
                pane.Hide()
                Profile_Set('Projects.Show', False)
                self._mi.Check(False)
            else:
                pane.Show()
                Profile_Set('Projects.Show', True)
                self._mi.Check(True)
            mw.Update()
        else:
            evt.Skip()

