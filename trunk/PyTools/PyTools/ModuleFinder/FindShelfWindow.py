# -*- coding: utf-8 -*-
# Name: FindShelfWindow.py
# Purpose: ModuleFinder plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import os.path
import wx

# Editra Libraries
import util
import eclib
import ed_msg
from syntax import syntax
import syntax.synglob as synglob

# Local imports
from PyTools.Common import ToolConfig
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.ModuleFinder.FindResultsList import FindResultsList
from PyTools.ModuleFinder.PythonModuleFinder import PythonModuleFinder

# Globals
_ = wx.GetTranslation
#-----------------------------------------------------------------------------#

class FindShelfWindow(BaseShelfWindow):
    """Module Find Results Window"""
    __moduleFinders = {
        synglob.ID_LANG_PYTHON: PythonModuleFinder
    }

    def __init__(self, parent):
        """Initialize the window"""
        super(FindShelfWindow, self).__init__(parent)

        # Setup
        ctrlbar = self.setup(FindResultsList(self))
        ctrlbar.AddStretchSpacer()
        txtentrysize = wx.Size(256, wx.DefaultSize.GetHeight())
        self.textentry = eclib.CommandEntryBase(ctrlbar, size=txtentrysize,
                                           style=wx.TE_PROCESS_ENTER|wx.WANTS_CHARS)
        ctrlbar.AddControl(self.textentry, wx.ALIGN_RIGHT)
        self.layout("Find", self.OnFindModule, self.OnJobTimer)

        # Attributes
        self._finder = None

    def _onmodulefind(self, editor, moduletofind):
        # With the text control (ed_stc.EditraStc) this will return the full
        # path of the file or a wx.EmptyString if the buffer does not contain
        # an on disk file
        filename = os.path.normcase(editor.GetFileName())
        self._listCtrl.Clear()

        vardict = {}
        if filename:
            filename = os.path.abspath(filename)
            fileext = os.path.splitext(filename)[1]
            if fileext:
                filetype = syntax.GetIdFromExt(fileext[1:]) # pass in file extension
                directoryvariables = self.get_directory_variables(filetype)
                if directoryvariables:
                    vardict = directoryvariables.read_dirvarfile(filename)

        self._findmodule(synglob.ID_LANG_PYTHON, vardict, moduletofind)
        self._hasrun = True

    def OnFindModule(self, event):
        editor = wx.GetApp().GetCurrentBuffer()
        wx.CallAfter(self._onmodulefind, editor, self.textentry.GetValue())

    def get_module_finder(self, filetype, vardict, moduletofind):
        try:
            return self.__moduleFinders[filetype](vardict, moduletofind)
        except:
            pass
        return None

    def _findmodule(self, filetype, vardict, moduletofind):
        modulefinder = self.get_module_finder(filetype, vardict, moduletofind)
        if not modulefinder:
            return
        self._finder = modulefinder
        self._module = moduletofind

        # Start job timer
        self._StopTimer()
        self._jobtimer.Start(250, True)

    def _OnFindData(self, data):
        """Find job callback
        @param data: PythonModuleFinder.FindResults

        """
        self._listCtrl.PopulateRows(data)
        self._listCtrl.RefreshRows()
        mwid = self.GetMainWindow().GetId()
        ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (mwid, False))

    def OnJobTimer(self, evt):
        """Start a module find job"""
        if self._finder:
            util.Log("[PyFind][info] module %s" % self._module)
            mwid = self.GetMainWindow().GetId()
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (mwid, True))
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_STATE, (mwid, -1, -1))
            self._finder.Find(self._OnFindData)
