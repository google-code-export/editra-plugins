# -*- coding: utf-8 -*-
# Name: __init__.py
# Purpose: Plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

# Plugin Metadata
"""
Upgrades Editra into a Python IDE, including syntax checking, module search and debugging

"""

__version__ = "0.1"
__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx

# Editra Libraries
import ed_glob
import iface
import plugin

# Local Imports
from PyStudio.Common import Images
from PyStudio.Common.ToolConfig import ToolConfigPanel
from PyStudio.Common.BaseShelfPlugin import BaseShelfPlugin
from PyStudio.SyntaxChecker.LintShelfWindow import LintShelfWindow
from PyStudio.SyntaxChecker.CompileChecker import CompileEntryPoint
from PyStudio.ModuleFinder.FindTabMenu import FindTabMenu
from PyStudio.ModuleFinder.FindShelfWindow import FindShelfWindow
from PyStudio.Debugger.DebugShelfWindow import DebugShelfWindow
from PyStudio.Debugger.BreakPointsShelfWindow import BreakPointsShelfWindow, BreakpointController
from PyStudio.Debugger.StackThreadShelfWindow import StackThreadShelfWindow
from PyStudio.Debugger.VariablesShelfWindow import VariablesShelfWindow
from PyStudio.Debugger.ExpressionsShelfWindow import ExpressionsShelfWindow
from PyStudio.Debugger.MessageHandler import MessageHandler
from PyStudio.Debugger.RpdbDebugger import RpdbDebugger

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

# Implementation
class PyLint(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyLint, self).__init__(pluginmgr, "PyLint", LintShelfWindow)

    def AllowMultiple(self):
        """Plugin allows multiple instances"""
        return True

    def InstallComponents(self, parent):
        """Initialize and install"""
        setattr(self, '_installed', True)
        CompileEntryPoint()

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        return Images.Lint.Bitmap

class PyFind(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyFind, self).__init__(pluginmgr, "PyFind", FindShelfWindow)

    def AllowMultiple(self):
        """Plugin allows multiple instances"""
        return True

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_FIND), wx.ART_MENU)
        return bmp

    def InstallComponents(self, parent):
        """Initialize and install"""
        setattr(self, '_installed', True)
        FindTabMenu() # Initialize singleton tab menu handler

    def IsInstalled(self):
        return getattr(self, '_installed', False)

class PyDebug(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyDebug, self).__init__(pluginmgr, "PyDebug", DebugShelfWindow)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        return Images.Bug.Bitmap

    def InstallComponents(self, parent):
        """Initialize and install"""
        setattr(self, '_installed', True)
        # Initialize singletons
        RpdbDebugger()
        MessageHandler()
        BreakpointController()

    def IsInstalled(self):
        return getattr(self, '_installed', False)

class PyBreakPoint(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyBreakPoint, self).__init__(pluginmgr, "PyBreakPoint", BreakPointsShelfWindow)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        return Images.Bug.Bitmap

class PyStackThread(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyStackThread, self).__init__(pluginmgr, "PyStackThread", StackThreadShelfWindow)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        return Images.Bug.Bitmap

class PyVariable(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyVariable, self).__init__(pluginmgr, "PyVariable", VariablesShelfWindow)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        return Images.Bug.Bitmap

class PyExpression(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyExpression, self).__init__(pluginmgr, "PyExpression", ExpressionsShelfWindow)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        return Images.Bug.Bitmap

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
        return _("PyStudio")
