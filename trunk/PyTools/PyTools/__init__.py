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

# Editra Libraries
import ed_glob
import iface
import plugin

# Local Imports
from PyTools.Common import Images
from PyTools.Common.ToolConfig import ToolConfigPanel
from PyTools.Common.BaseShelfPlugin import BaseShelfPlugin
from PyTools.SyntaxChecker.LintShelfWindow import LintShelfWindow
from PyTools.ModuleFinder.FindShelfWindow import FindShelfWindow
from PyTools.Debugger.DebugShelfWindow import DebugShelfWindow
from PyTools.Debugger.BreakPointsShelfWindow import BreakPointsShelfWindow
from PyTools.Debugger.StackFrameShelfWindow import StackFrameShelfWindow
from PyTools.Debugger.ThreadsShelfWindow import ThreadsShelfWindow
from PyTools.Debugger.VariablesShelfWindows import LocalVariablesShelfWindow
from PyTools.Debugger.VariablesShelfWindows import GlobalVariablesShelfWindow
from PyTools.Debugger.VariablesShelfWindows import ExceptionsShelfWindow

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation
#-----------------------------------------------------------------------------#

# Implementation
class PyLint(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyLint, self).__init__(pluginmgr, "PyLint", LintShelfWindow)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        return Images.Lint.Bitmap

class PyFind(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyFind, self).__init__(pluginmgr, "PyFind", FindShelfWindow)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_FIND), wx.ART_MENU)
        return bmp

class PyDebug(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyDebug, self).__init__(pluginmgr, "PyDebug", DebugShelfWindow)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        return Images.Bug.Bitmap

class PyBreakPoint(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyBreakPoint, self).__init__(pluginmgr, "PyBreakPoint", BreakPointsShelfWindow)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        return Images.Bug.Bitmap

class PyStackFrame(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyStackFrame, self).__init__(pluginmgr, "PyStackFrame", StackFrameShelfWindow)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        return Images.Bug.Bitmap

class PyThread(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyThread, self).__init__(pluginmgr, "PyThread", ThreadsShelfWindow)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        return Images.Bug.Bitmap

class PyLocalVariable(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyLocalVariable, self).__init__(pluginmgr, "PyLocalVariable", LocalVariablesShelfWindow)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        return Images.Bug.Bitmap

class PyGlobalVariable(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyGlobalVariable, self).__init__(pluginmgr, "PyGlobalVariable", GlobalVariablesShelfWindow)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        return Images.Bug.Bitmap

class PyException(BaseShelfPlugin):
    """Script Launcher and output viewer"""
    def __init__(self, pluginmgr):
        super(PyException, self).__init__(pluginmgr, "PyException", ExceptionsShelfWindow)

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
        return _("PyTools")
