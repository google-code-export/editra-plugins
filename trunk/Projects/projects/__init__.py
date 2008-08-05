# -*- coding: utf-8 -*-

""" Adds a sidepanel that incorporates file management and source control """

__author__ = "Kevin D. Smith <Kevin.Smith@sixquickrun.com>"
__revision__ = "$Revision$"
__scid__ = "$Id$"
__version__ = "0.6"

#-----------------------------------------------------------------------------#
# Imports
import wx 

# Editra Libraries
import plugin 
import ed_glob
import iface
import ed_menu
import util
from ProjectPane import ProjectPane

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation
PANE_NAME = ProjectPane.PANE_NAME

# Try and add this plugins message catalogs to the app
try:
    wx.GetApp().AddMessageCatalog('Projects', __name__)
except:
    pass

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

            mgr.Update()

    def GetMenuHandlers(self):
        """Returns the menu event handlers"""
        return [(ProjectPane.ID_PROJECTS, self._projects.OnShowProjects)]

    def GetMinVersion(self):
        """Get the minimum version of Editra that this plugin supports"""
        return "0.3.15"

    def GetUIHandlers(self):
        """Returns handlers for UpdateUI events"""
        return [(ProjectPane.ID_PROJECTS, self._projects.OnUpdateMenu)]
