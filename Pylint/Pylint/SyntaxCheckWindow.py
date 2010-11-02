# -*- coding: utf-8 -*-
# Name: SyntaxCheckWindow.py                                                           
# Purpose: Pylint plugin                                              
# Author: Mike Rans                              
# Copyright: (c) 2010 Mike Rans                                
# License: wxWindows License                                                  
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id $"
__revision__ = "$Revision $"

#-----------------------------------------------------------------------------#
# Imports
import os
import wx

# Editra Libraries
import util
import ed_msg
from syntax import syntax
import syntax.synglob as synglob

# Local imports
from CheckResultsList import CheckResultsList

# Syntax checkers
from PythonSyntaxChecker import PythonSyntaxChecker

# Directory Variables
from PythonDirectoryVariables import PythonDirectoryVariables

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

#-----------------------------------------------------------------------------#

class SyntaxCheckWindow(wx.Panel):
    """Syntax Check Results Window"""
    __syntaxCheckers = {
        synglob.ID_LANG_PYTHON: PythonSyntaxChecker
    }

    __directoryVariables = {
        synglob.ID_LANG_PYTHON: PythonDirectoryVariables
    }
    def __init__(self, parent):
        """Initialize the window"""
        super(SyntaxCheckWindow, self).__init__(parent)

        # Attributes
        # Parent is ed_shelf.EdShelfBook
        self._mw = self.__FindMainWindow()
        self._log = wx.GetApp().GetLog()
        self._listCtrl = CheckResultsList(
            self, style=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_SORT_ASCENDING
        )

        self._listCtrl.set_mainwindow(self._mw)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self._listCtrl, 1, wx.EXPAND|wx.ALL)
        self.SetSizer(vbox)

        # Editra Message Handlers
        ed_msg.Subscribe(self.OnFileLoad, ed_msg.EDMSG_FILE_OPENED)
        ed_msg.Subscribe(self.OnFileSave, ed_msg.EDMSG_FILE_SAVED)
        ed_msg.Subscribe(self.OnPosChange, ed_msg.EDMSG_UI_STC_POS_CHANGED)
        ed_msg.Subscribe(self.OnPageChanged, ed_msg.EDMSG_UI_NB_CHANGED)
        ed_msg.Subscribe(self.OnChange, ed_msg.EDMSG_UI_STC_CHANGED)
        
    def __del__(self):
        ed_msg.Unsubscribe(self.OnFileLoad, ed_msg.EDMSG_FILE_OPENED)
        ed_msg.Unsubscribe(self.OnFileSave, ed_msg.EDMSG_FILE_SAVED)
        ed_msg.Unsubscribe(self.OnPosChange, ed_msg.EDMSG_UI_STC_POS_CHANGED)
        ed_msg.Unsubscribe(self.OnPageChanged, ed_msg.EDMSG_UI_NB_CHANGED)
        ed_msg.Unsubscribe(self.OnChange, ed_msg.EDMSG_UI_STC_CHANGED)

    def GetMainWindow(self):
        return self._mw

    def __FindMainWindow(self):
        """Find the mainwindow of this control
        @return: MainWindow or None

        """
        def IsMainWin(win):
            """Check if the given window is a main window"""
            return getattr(tlw, '__name__', '') == 'MainWindow'

        tlw = self.GetTopLevelParent()
        if IsMainWin(tlw):
            return tlw
        elif hasattr(tlw, 'GetParent'):
            tlw = tlw.GetParent()
            if IsMainWin(tlw):
                return tlw

        return None

    def _onfileaccess(self, editor):
        # With the text control (ed_stc.EditraStc) this will return the full
        # path of the file or a wx.EmptyString if the buffer does not contain
        # an on disk file
        filename = editor.GetFileName()
        self._listCtrl.set_editor(editor)
        with FreezeDrawer(self._listCtrl):
            self._listCtrl.DeleteOldRows()

        if not filename:
            return

        filename = os.path.abspath(filename)
        fileext = os.path.splitext(filename)[1]
        if fileext == u"":
            return

        filetype = syntax.GetIdFromExt(fileext[1:]) # pass in file extension
        directoryvariables = self.get_directory_variables(filetype)
        if directoryvariables:
            vardict = directoryvariables.read_dirvarfile(filename)
        else:
            vardict = {}

        self._checksyntax(filetype, vardict, filename)
        if directoryvariables:
            directoryvariables.close()
        
    def OnPageChanged(self, msg):
        """ Notebook tab was changed """
        notebook, pg_num = msg.GetData()
        editor = notebook.GetPage(pg_num)
        wx.CallAfter(self._onfileaccess, editor)

    def OnFileLoad(self, msg):
        """Load File message"""
        editor = self._GetEditorForFile(msg.GetData())
        wx.CallAfter(self._onfileaccess, editor)
        
    def OnFileSave(self, msg):
        """Load File message"""
        filename, _ = msg.GetData()
        editor = self._GetEditorForFile(filename)
        wx.CallAfter(self._onfileaccess, editor)

    def get_syntax_checker(self, filetype, vardict, filename):
        try:
            return self.__syntaxCheckers[filetype](vardict, filename)
        except Exception:
            pass
        return None
        
    def get_directory_variables(self, filetype):
        try:
            return self.__directoryVariables[filetype]()
        except Exception:
            pass
        return None
        
    def _checksyntax(self, filetype, vardict, filename):
        syntaxchecker = self.get_syntax_checker(filetype, vardict, filename)
        if not syntaxchecker:
            return
        util.Log("[PyLint][info] fileName %s" % (filename))
        mwid = self.GetMainWindow().GetId()
        ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (mwid, True))
        ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_STATE, (mwid, -1, -1))
        
        #Something like [('Syntax Error', '__all__ = ["CSVSMonitorThread"]', 7)]
        syntaxchecker.Check(self._OnSyntaxData)

    def _OnSyntaxData(self, data):
        with FreezeDrawer(self._listCtrl):
            if len(data) != 0:
                self._listCtrl.PopulateRows(data)
                self._listCtrl.RefreshRows()
        mwid = self.GetMainWindow().GetId()
        ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (mwid, False))

    def OnChange(self, posdict):
        wx.CallAfter(self.delete_rows)
        
    def delete_rows(self):
        with FreezeDrawer(self._listCtrl):
            self._listCtrl.DeleteOldRows()
            
    def OnPosChange(self, msg):
        lineno = msg.GetData()["lnum"]
        wx.CallAfter(self._listCtrl.show_calltip, lineno)

    def _GetEditorForFile(self, fname):
        """Return the EdEditorView that's managing the file, if available
        @param fname: File name to open
        @param mainw: MainWindow instance to open the file in
        @return: Text control managing the file
        @rtype: ed_editv.EdEditorView
        
        """
        nb = self._mw.GetNotebook()
        for page in nb.GetTextControls():
            if page.GetFileName() == fname:
                return nb.GetPage(page.GetTabIndex())
        
        return None
    