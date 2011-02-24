# -*- coding: utf-8 -*-
# Name: PyToolsUtils.py
# Purpose: Utility functions
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" Utility functions """

__version__ = "0.2"
__author__ = "Mike Rans"
__svnid__ = "$Id: PyToolsUtils.py 1025 2010-12-24 18:30:23Z rans@email.com $"
__revision__ = "$Revision: 1025 $"

#-----------------------------------------------------------------------------#
# Imports
import wx
import threading
import os.path

# Editra imports
import ebmlib
import util

# Globals
_ = wx.GetTranslation

class PyToolsUtils():

    @staticmethod
    def get_packageroot(filepath):
        # traverse downwards until we are out of a python package
        fullPath = os.path.abspath(filepath)
        parentPath, childPath = os.path.dirname(fullPath), os.path.basename(fullPath)

        while parentPath != "/" and os.path.exists(os.path.join(parentPath, '__init__.py')):
            childPath = os.path.join(os.path.basename(parentPath), childPath)
            parentPath = os.path.dirname(parentPath)
        return (childPath, parentPath)

    @staticmethod
    def get_modulepath(childPath):
        return os.path.splitext(childPath)[0].replace(os.path.sep, ".")

    @staticmethod
    def GetDefaultPython():
        if wx.Platform == "__WXMSW__":
            pythonpath = ebmlib.Which("python.exe")
        else:
            pythonpath = ebmlib.Which("python")
        if pythonpath:
            return pythonpath
        return u""

    @staticmethod
    def GetDefaultScript(script, pythonpath=None):
        if wx.Platform == "__WXMSW__":
            path = ebmlib.Which("%s.bat" % script)
        else:
            path = ebmlib.Which(script)
        if path:
            return path
        if pythonpath:
            path = os.path.dirname(pythonpath)
            if wx.Platform == "__WXMSW__":
                path = os.path.join(path, "Scripts", script)
            else:
                path = "/usr/local/bin/%s" % script
            if os.path.isfile(path):
                return path
        return u""

    @staticmethod
    def GetEditorForFile(mainw, fname):
        """Return the EdEditorView that's managing the file, if available
        @param fname: File name to open
        @param mainw: MainWindow instance to open the file in
        @return: Text control managing the file
        @rtype: ed_editv.EdEditorView

        """
        nb = mainw.GetNotebook()
        for page in nb.GetTextControls():
            if page.GetFileName() == fname:
                return nb.GetPage(page.GetTabIndex())

        return None

#-----------------------------------------------------------------------------#

class RunProcInThread(threading.Thread):
    """Background thread to run task in"""
    def __init__(self, fn, target, desc):
        """@param fn: function to run
        @param target: callable(data) To receive output data
        @param desc: description of task
        """
        super(RunProcInThread, self).__init__()

        # Attributes
        self.fn = fn
        self.target = target
        self.desc = desc

    def run(self):
        try:
            data = self.fn()
        except Exception, msg:
            util.Log("[%s][err] %s Failure: %s" % (self.desc, self.desc, msg))
            data = [(u"Error", unicode(msg), -1)]
        if self.target:
            wx.CallAfter(self.target, data)

class FreezeDrawer(object):
    """To be used in 'with' statements. Upon enter freezes the drawing
    and thaws upon exit.

    """
    def __init__(self, wnd):
        self._wnd = wnd

    def __enter__(self):
        self._wnd.Freeze()

    def __exit__(self, eT, eV, tB):
        self._wnd.Thaw()
