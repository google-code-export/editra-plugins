# -*- coding: utf-8 -*-
# Name: __init__.py
# Purpose: Pylint plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

# Plugin Metadata
"""
Adds Python syntax checking using Pylint with results in a Shelf window.

"""

__version__ = "0.1"
__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx

# Editra imports
import ed_glob
import iface
import plugin
import util

# Local Imports
from SyntaxCheckWindow import SyntaxCheckWindow
import ToolConfig

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#
# Implementation
class Pylint(plugin.Plugin):
    """Script Launcher and output viewer"""
    plugin.Implements(iface.ShelfI)
    ID_PYLINT = wx.NewId()
    INSTALLED = False
    SHELF = None

    @property
    def __name__(self):
        return u'Pylint'

    def AllowMultiple(self):
        """PyLint allows multiple instances"""
        return True

    def CreateItem(self, parent):
        """Create a PyLint panel"""
        util.Log("[PyLint][info] Creating Pylint instance for Shelf")
        return SyntaxCheckWindow(parent)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_BIN_FILE), wx.ART_MENU)
        return bmp

    def GetId(self):
        """The unique identifier of this plugin"""
        return self.ID_PYLINT

    def GetMenuEntry(self, menu):
        """This plugins menu entry"""
        item = wx.MenuItem(menu, self.ID_PYLINT, self.__name__,
                           _("Show Pylint checker"))
        item.SetBitmap(self.GetBitmap())
        return item

    def GetMinVersion(self):
        """Minimum version of Editra this plugin is compatible with"""
        return "5.99"

    def GetName(self):
        """The name of this plugin"""
        return self.__name__

    def InstallComponents(self, mainw):
        """Install extra menu components
        param mainw: MainWindow Instance

        """
        pass

    def IsInstalled(self):
        """Check whether PyLint has been installed yet or not
        @note: overridden from Plugin
        @return bool

        """
        return Pylint.INSTALLED

    def IsStockable(self):
        """This item can be reloaded between sessions"""
        return True

#-----------------------------------------------------------------------------#
# Configuration Interface

def GetConfigObject():
    return ConfigObject()

class ConfigObject(plugin.PluginConfigObject):
    """Plugin configuration object for PyLint
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
        return _("PyLint")
