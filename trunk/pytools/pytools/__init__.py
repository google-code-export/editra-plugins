###############################################################################
# Name: __init__.py                                                           #
# Purpose: Python Tools plugin                                                #
# Author: Ofer Schwarz <os.urandom@gmail.com>,                                #
#         Rudi Pettazzi <rudi.pettazzi@gmail.com>                             #
# Copyright: (c) 2008 Ofer Schwarz <os.urandom@gmail.com>                     #
# Licence: wxWindows Licence                                                  #
###############################################################################

"""Various Python tools for Editra"""

# Plugin Meta Data
__author__ = "Ofer Schwarz, Rudi Pettazzi, Alexey Zankevich"
__version__ = "0.1"

#-----------------------------------------------------------------------------#
# Imports
import os
import re
import sys
import platform
from StringIO import StringIO
import wx

# Editra Imports
import iface
import plugin
import ed_msg
from profiler import Profile_Get, Profile_Set

# Local Imports
from openmodule import OpenModuleDialog, ID_OPEN_MODULE
from varchecker import HighLight
import finder
import ptcfg

try:
    from foxtrot import check_vars
except ImportError, e:
    raise ImportError('Please, install foxtrot package at first!')

#-----------------------------------------------------------------------------#
# Globals

_ = wx.GetTranslation
PYTOOLS_PREFS = 'PyTools.Prefs'
PYTOOLS_BASE_PATH_CHOOSE_MSG  = _("Select Python library directory (ex: %s): ")
PYTOOLS_BASE_PATH_INVALID_MSG = _("""%s doesn't appear to be valid. 
The selected directory should contain the site-packages subdirectory""")

#-----------------------------------------------------------------------------#

class PyTools(plugin.Plugin):
    """ Adds Python tools to the Editra menus """
    plugin.Implements(iface.MainWindowI)

    def PlugIt(self, parent):
        """Add menu entries"""
        if parent:
            # Use Editra's logging system
            self._log = wx.GetApp().GetLog()
            self._log("[pytools][info] Installing Pytools")
            self._finder = None
            # Install all tools
            self.lighter = HighLight(parent)
            self.lighter.PlugIt()
            self.InstallOpenModule(parent)
        else:
            self._log("[pytools][err] Failed to install pytools plugin")

    def InstallOpenModule(self, parent):
        self._log("[pytools][info] Installing module opener")
        file_menu = parent.GetMenuBar().GetMenuByName("file")
        # Insert the Open Module command before Open Recent
        # TODO: Find the 'open recent' position in a more generic way
        # NOTE:CJP you can use the FindById method of wxMenu to do this
        file_menu.Insert(4, ID_OPEN_MODULE,
                _("Open Python &Module\tCtrl+Shift+M"),
                _("Open the source code of a Python module from sys.path"))

    def GetMenuHandlers(self):
        """This is used to register the menu handler with the app and
        associate the event with the parent window. It needs to return
        a list of ID/Handler pairs for each menu handler that the plugin
        is providing.

        """
        return [(ID_OPEN_MODULE, self.OnOpenModule)]

    def GetUIHandlers(self):
        """This is used to register the update ui handler with the app and
        associate the event with the parent window. This plugin doesn't use
        the UpdateUI event so it can just return an empty list.

        """
        return list()

    def OnOpenModule(self, evt):
        """Show the OpenModule dialog"""
        if evt.GetId() != ID_OPEN_MODULE:
            evt.Skip()

        win = wx.GetApp().GetActiveWindow()

        if self._finder == None:
            prefs = Profile_Get(PYTOOLS_PREFS, default=dict())
            base = prefs.get('module_base')
            if not base or not CheckModuleBase(base):
                base = ChooseModuleBase(win)
            if base:
                prefs['module_base'] = base
                self._log("[pytools][debug] Saving base search dir: %s" % base)
                Profile_Set(PYTOOLS_PREFS, prefs)
                path = finder.GetSearchPath(base)
                self._log("[pytools][debug] search path: %s" % path)
                self._finder = finder.ModuleFinder(path)
            else:
                return

        mdlg = OpenModuleDialog(win, self._finder, title=_("Open module"))
        mdlg.SetFocus()
        
        if mdlg.ShowModal() != wx.ID_OK:
            mdlg.Destroy()
            return

        filename = mdlg.GetValue()
        if filename:
            mdlg.Destroy()
            win.DoOpen(evt, filename)

def CheckModuleBase(base):
    if sys.platform == 'win32':
        spkg = os.path.join(base, 'lib', 'site-packages')
    else:
        spkg = os.path.join(base, 'site-packages')
    return base != None and os.path.exists(base) and os.path.isdir(base) \
            and os.path.exists(spkg)

# XXX investigate python installation layout on MacOSX ("apple python" vs. 
# default python install
def ChooseModuleBase(parent):
    """Shows a dialog to choose the python libraries directory.
    @return: the python installation libraries root (the directory containing, 
             among the others, the site-packages dir) or None if the user
             didn't make any choice or choose an invalid path
    """
    if sys.platform == 'win32':
        ex = "C:\Python26"
    elif platform.mac_ver()[0]:
        ex = "/Library/Frameworks/Python.framework/2.6"
    else:
        ex = "/usr/lib/python-2.6"

    title = PYTOOLS_BASE_PATH_CHOOSE_MSG % ex
    value = None
    dlg = wx.DirDialog(parent, title,
                       style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
    if dlg.ShowModal() == wx.ID_OK:
        value = dlg.GetPath()
        
    if not CheckModuleBase(value):
        errmsg = PYTOOLS_BASE_PATH_INVALID_MSG % value
        errdlg = wx.MessageDialog(dlg, errmsg, 
                                _('Error'),  wx.OK | wx.ICON_ERROR)
        if errdlg.ShowModal() == wx.ID_OK:
            errdlg.Destroy()
        value = None

    dlg.Destroy()
    return value

#-----------------------------------------------------------------------------#
# Plugin Configuration Interface Implementation

def GetConfigObject():
    return PyToolsConfigObject()

class PyToolsConfigObject(plugin.PluginConfigObject):
    """Plugin configuration object. Plugins that wish to provide a
    configuration panel should implement a subclass of this object
    in their __init__ module.

    """
    def GetConfigPanel(self, parent):
        """Get the configuration panel for this plugin
        @param parent: parent window for the panel
        @return: wxPanel

        """
        return ptcfg.PyToolsCfgPanel(parent)

    def GetLabel(self):
        """Get the label for this config panel
        @return string

        """
        return _("PyTools")

