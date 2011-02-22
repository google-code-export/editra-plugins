# -*- coding: utf-8 -*-
# Name: __init__.py
# Purpose: Plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

# Plugin Metadata
"""
Adds shelf windows

"""

__version__ = "0.1"
__author__ = "Mike Rans"
__svnid__ = "$Id: __init__.py 1058 2011-02-14 20:44:05Z rans@email.com $"
__revision__ = "$Revision: 1058 $"

#-----------------------------------------------------------------------------#
# Imports
import wx

# Editra imports
import ed_glob
import iface
import plugin
import util

# Local Imports
from PyTools.Common.ToolConfig import ToolConfigPanel
from PyTools.Common.BaseShelfPlugin import BaseShelfPlugin
from PyTools.SyntaxChecker.LintShelfWindow import LintShelfWindow
from PyTools.ModuleFinder.FindShelfWindow import FindShelfWindow
from PyTools.Debugger.DebugShelfWindow import DebugShelfWindow

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#
# Implementation
class PyLint(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyLint, self).__init__(pluginmgr, "PyLint", LintShelfWindow)

class PyFind(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyFind, self).__init__(pluginmgr, "PyFind", FindShelfWindow)

class PyDebug(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyDebug, self).__init__(pluginmgr, "PyDebug", DebugShelfWindow)

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
        return ToolConfigPanel(parent)

    def GetLabel(self):
        """Get the label for this config panel
        @return string

        """
        return _("PyTools")
