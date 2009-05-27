# -*- coding: utf-8 -*-
###############################################################################
# Name: __init__.py                                                           #
# Purpose: Syntax Checker plugin                                              #
# Author: Giuseppe "Cowo" Corbelli                                            #
# Copyright: (c) 2009 Giuseppe "Cowo" Corbelli                                #
# License: wxWindows License                                                  #
###############################################################################

"""Editra Shelf display window"""

__author__ = "Giuseppe 'Cowo' Corbelli"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx
import wx.lib.mixins.listctrl as mixins

# Editra Libraries
import util
import ed_msg
import syntax.synglob as synglob
import eclib.elistmix as elistmix

# Syntax checkers
from PhpSyntaxChecker import PhpSyntaxChecker
from PythonSyntaxChecker import PythonSyntaxChecker

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

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
        synglob.ID_LANG_PYTHON: PythonSyntaxChecker,
        synglob.ID_LANG_PHP: PhpSyntaxChecker
    }

    def __init__(self, parent):
        """Initialize the window"""
        wx.Panel.__init__(self, parent)

        # Attributes
        self._mw = parent
        self._log = wx.GetApp().GetLog()
        self._listCtrl = CheckResultsList(
            self, style=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_SORT_ASCENDING
        )

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self._listCtrl, 1, wx.EXPAND|wx.ALL)
        self.SetSizer(vbox)
        self.SetAutoLayout(True)

        ed_msg.Subscribe(self.OnFileSaved, ed_msg.EDMSG_FILE_SAVED)

    def __del__(self):
        ed_msg.Unsubscribe(self.OnFileSaved, ed_msg.EDMSG_FILE_SAVED)

    @ed_msg.mwcontext
    def OnFileSaved(self, arg):
        """File Saved message"""
        (fileName, fileType) = arg.GetData()
        util.Log("[SyntaxCheckWindow][info] fileName %s" % (fileName))
        try:
            syntaxChecker = self.__syntaxCheckers[fileType]
        except Exception, msg:
            util.Log("[SyntaxCheckWindow][info] Error while checking %s: %s" % (fileName, msg))
            return

        data = syntaxChecker.Check(fileName)
#        with FreezeDrawer(self._listCtrl):
        self._listCtrl.Freeze()
        self._listCtrl.DeleteAllItems()

        if len(data) == 0:
            self._listCtrl.Thaw()
            return

        self._listCtrl.PopulateRows(fileName, data)
        self._listCtrl.RefreshRows()
        self._listCtrl.Thaw()

#-----------------------------------------------------------------------------#

class CheckResultsList(wx.ListCtrl,
                       mixins.ListCtrlAutoWidthMixin,
                       elistmix.ListRowHighlighter):
    """List control for displaying syntax check results"""
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        mixins.ListCtrlAutoWidthMixin.__init__(self)
        elistmix.ListRowHighlighter.__init__(self)

        # Attributes
        self._mainw = self.__FindMainWindow()
        self._errs = list()

        # Setup
        self.InsertColumn(0, _("Type"))
        self.InsertColumn(1, _("Error"))
        self.InsertColumn(2, _("File"))
        self.InsertColumn(3, _("Line"))
        self.setResizeColumn(0)
        self.setResizeColumn(1)
        self.setResizeColumn(2)
        self.setResizeColumn(3)

        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivate)

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

    def OnItemActivate(self, evt):
        """Go to the error in the file"""
        idx = evt.GetIndex()
        if idx < len(self._errs):
            fname, line = self._errs[idx]
            try:
                _OpenToLine(fname, max(0, line - 1), self._mainw)
            except:
                pass

    def PopulateRows(self, filename, data):
        """Populate the list with the data
        @param filename: string
        @param data: list of tuples

        """
        del self._errs
        self._errs = list()
        for (eType, eText, eLine) in data:
            self.Append((unicode(eType), unicode(eText),
                        filename, unicode(eLine)))
            self._errs.append((filename, eLine))

#-----------------------------------------------------------------------------#

def _OpenToLine(fname, line, mainw):
    """Open the given filename to the given line number
    @param fname: File name to open, relative paths will be converted to abs
                  paths.
    @param line: Line number to set the cursor to after opening the file
    @param mainw: MainWindow instance to open the file in

    """
    nb = mainw.GetNotebook()
    buffers = [ page.GetFileName() for page in nb.GetTextControls() ]
    if fname in buffers:
        page = buffers.index(fname)
        nb.ChangePage(page)
        nb.GetPage(page).GotoLine(line)
    else:
        nb.OnDrop([fname])
        nb.GetPage(nb.GetSelection()).GotoLine(line)
