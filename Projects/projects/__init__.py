# -*- coding: utf-8 -*-

""" Adds a sidepanel that incorporates file management and source control """

__author__ = "Kevin D. Smith <Kevin.Smith@sixquickrun.com>"
__revision__ = "$Revision$"
__scid__ = "$Id$"
__version__ = "0.3"

#-----------------------------------------------------------------------------#
# Imports
import wx 

try:
    from pkg_resources import resource_filename
except ImportError:
    from extern.pkg_resources import resource_filename

# Editra Libraries
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

def InstallCatalogs():
    """Add this plugins message catalogs to the app's locale object.
    the Catalog name must be the name of the file in locale dir without the
    extension.

    """
    locale = wx.GetApp().GetLocaleObject()
    if locale is not None:
        path = resource_filename(__name__, 'locale')
        locale.AddCatalogLookupPathPrefix(path)
        locale.AddCatalog(PANE_NAME)

# Might error out is used in a version of Editra < 0.2.65
try:
    InstallCatalogs()
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
