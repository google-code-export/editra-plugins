# -*- coding: utf-8 -*-

""" Adds a sidepanel that incorporates file management and source control """

__author__ = "Kevin D. Smith <Kevin.Smith@sixquickrun.com>"
__revision__ = "$Revision$"
__scid__ = "$Id$"
__version__ = "0.1"

#-----------------------------------------------------------------------------#
# Imports
import wx 
import plugin 
import ed_glob
import iface
import ed_menu
import util
from profiler import Profile_Get, Profile_Set
from ProjectPane import ProjectPane

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation
PANE_NAME = ProjectPane.PANE_NAME

#-----------------------------------------------------------------------------#

class Projects(plugin.Plugin):
    """Adds a projects pane to the view menu"""
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        """Adds the view menu entry and registers the event handler"""
        mainw = parent
        if mainw != None:
            util.Log("[projects][info] Installing projects plugin")

            self._projects = ProjectPane(mainw)
            mgr = mainw.GetFrameManager()
            mgr.AddPane(self._projects, wx.aui.AuiPaneInfo().Name(PANE_NAME).\
                        Caption("Projects").Left().Layer(1).\
                        CloseButton(True).MaximizeButton(False).\
                        BestSize(wx.Size(215, 350)))

            # Get settings from profile
            if Profile_Get('Projects.Show', 'bool', False):
                mgr.GetPane(PANE_NAME).Show()
            else:
                mgr.GetPane(PANE_NAME).Hide()

            mgr.Update()

            # Event Handlers
            mainw.Bind(wx.aui.EVT_AUI_PANE_CLOSE, self.OnPaneClose)

    def GetMenuHandlers(self):
        """Returns the menu event handlers"""
        return [(self._projects.ID_PROJECTS, self._projects.OnShowProjects)]

    def GetUIHandlers(self):
        """Returns handlers for UpdateUI events"""
        return list()

    def OnPaneClose(self, evt):
        """ Handles when the pane is closed to update the profile """
        pane = evt.GetPane()
        if pane.name == PANE_NAME:
            util.Log('[projects][info] Closed Projects pane')
            Profile_Set('Projects.Show', False)
        else:
            evt.Skip()
