# -*- coding: utf-8 -*-
# Name: __init__.py
# Purpose: PyTools plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

# Plugin Metadata
"""
Adds Python syntax checking using Pylint and debugging using Winpdb with results in a Shelf window.

"""

__version__ = "0.1"
__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import os
import sys
import wx

# Editra imports
import ed_glob
import iface
import plugin
import util
from profiler import Profile_Get, Profile_Set

# Local Imports
import ToolConfig
from ToolConfig import PYTOOL_CONFIG
from openmodule import OpenModuleDialog, ID_OPEN_MODULE
from ShelfWindow import ShelfWindow
#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation
#-----------------------------------------------------------------------------#
# Implementation
class PyTools(plugin.Plugin):
    """Script Launcher and output viewer"""
    plugin.Implements(iface.ShelfI)
    ID_PYTOOLS = wx.NewId()
    INSTALLED = False
    SHELF = None

    @property
    def __name__(self):
        return u'PyTools'

    def AllowMultiple(self):
        """PyTools allows multiple instances"""
        return True

    def CreateItem(self, parent):
        """Create a PyTools panel"""
        util.Log("[PyTools][info] Creating PyTools instance for Shelf")
        return ShelfWindow(parent)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_BIN_FILE), wx.ART_MENU)
        return bmp

    def GetId(self):
        """The unique identifier of this plugin"""
        return self.ID_PYTOOLS

    def GetMenuEntry(self, menu):
        """This plugins menu entry"""
        item = wx.MenuItem(menu, self.ID_PYTOOLS, self.__name__,
                           _("Show PyTools"))
        item.SetBitmap(self.GetBitmap())
        return item

    def GetMinVersion(self):
        """Minimum version of Editra this plugin is compatible with"""
        return "5.99"

    def GetName(self):
        """The name of this plugin"""
        return self.__name__

    def InstallOpenModule(self, parent):
        util.Log("[PyTools][info] Installing module opener")
        file_menu = parent.GetMenuBar().GetMenuByName("file")
        # Insert the Open Module command before Open Recent
        # TODO: Find the 'open recent' position in a more generic way
        # NOTE:CJP you can use the FindById method of wxMenu to do this
        file_menu.Insert(4, ID_OPEN_MODULE,
                _("Open Python &Module\tCtrl+Shift+M"),
                _("Open the source code of a Python module from sys.path"))

    def InstallComponents(self, mainw):
        """Install extra menu components
        param mainw: MainWindow Instance

        """
        self.InstallOpenModule(mainw)
        mainw.AddMenuHandler(ID_OPEN_MODULE, self.OnOpenModule)

    def IsInstalled(self):
        """Check whether PyTools has been installed yet or not
        @note: overridden from Plugin
        @return bool

        """
        return PyTools.INSTALLED

    def IsStockable(self):
        """This item can be reloaded between sessions"""
        return True

    def OnOpenModule(self, evt):
        """Show the OpenModule dialog"""
        win = wx.GetApp().GetActiveWindow()

        mdlg = OpenModuleDialog(win, title=_("Open module"))
        mdlg.SetFocus()

        if mdlg.ShowModal() != wx.ID_OK:
            mdlg.Destroy()
            return

        filename = mdlg.GetValue()
        if filename:
            mdlg.Destroy()
            win.DoOpen(evt, filename)

#-----------------------------------------------------------------------------#
# Configuration Interface

def GetConfigObject():
    return ConfigObject()

class ConfigObject(plugin.PluginConfigObject):
    """Plugin configuration object for PyTools
    Provides configuration panel for plugin dialog.

    """
    def GetConfigPanel(self, parent):
        """Get the configuration panel for this plugin
        @param parent: parent window for the panel
        @return: wxPanel

        """
        return ToolConfig.ToolConfigPanel(parent)

    def GetLabel(self):
        """Get the label for this config panel
        @return string

        """
        return _("PyTools")
