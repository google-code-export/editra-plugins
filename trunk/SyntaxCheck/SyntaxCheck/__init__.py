#!/usr/bin/python
# -*- coding: utf-8 -*-
# Name: __init__.py
# Purpose: Syntax Checker plugin
# Author: Giuseppe "Cowo" Corbelli
# Copyright: (c) 2009 Giuseppe "Cowo" Corbelli
# License: wxWindows License
# Plugin Metadata
""" Syntax checker plugin.
It's a simple Shelf window that can do syntax checking for some kind of files.
Syntax checking is triggered by the Save action.
Currently supported languages are:
  - python: check implemented by means of compile() function
  - php: check implemented by "php -l" execution
"""
__version__ = "0.1"

__author__ = "Giuseppe 'Cowo' Corbelli"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx
import subprocess
import re

# Editra imports
import ed_glob
import iface
import plugin
import ed_msg
import util
import syntax.synglob as synglob
import syntax.synextreg as synextreg
import eclib.ctrlbox as ctrlbox
from ed_menu import EdMenuBar

#-----------------------------------------------------------------------------#

_ = wx.GetTranslation

#-----------------------------------------------------------------------------#
# Globals

class FreezeDrawer(object):
    def __init__(self, listCtrl):
        self._listCtrl = listCtrl
    def __enter__(self):
        self._listCtrl.Freeze()
    def __exit__(self, eT, eV, tB):
        self._listCtrl.Thaw()

#-----------------------------------------------------------------------------#
class AbstractSyntaxChecker(object):
    @staticmethod
    def Check(fileName):
        """ Return a list of
            [ (Type, error, line), ... ]
        """
        pass

class PhpSyntaxChecker(AbstractSyntaxChecker):
    reobj = re.compile('PHP\s+Parse\s+error:\s+(?P<type>.+?),\s*(?P<error>.+)\s+in\s+(?P<file>.+)\s+on line\s+(?P<line>\d+).*', re.I)
    @staticmethod
    def Check(fileName):
        try:
            pipe = subprocess.Popen(
                "php -l %s" % fileName, shell=False, stdout=subprocess.PIPE, stdin=None, stderr=subprocess.PIPE
            )
            retcode = pipe.wait()
        except OSError, e:
            return [ ("PHP execution error", str(e), None) ]
        except ValueError, e:
            return [ ("Popen() invalid args", str(e), None) ]
        except Exception, e:
            return [ ("Unknown Error", str(e), None) ]

        #No errors
        if (retcode == 0):
            return []
        errors = []
        for line in pipe.stderr:
            mObj = PhpSyntaxChecker.reobj.match(line.strip())
            if mObj is None:
                continue
            errors.append(
                (mObj.group('type'), mObj.group('error'), mObj.group('line'))
            )
        return errors

class PythonSyntaxChecker(AbstractSyntaxChecker):
    @staticmethod
    def Check(fileName):
        try:
            fd = open(fileName, 'r')
            code = fd.read().replace('\r\n', '\n').replace('\r', '\n')
            compile(code, fileName, 'exec')
        except SyntaxError, e:
            return [ ("Syntax Error", e.text.rstrip(), e.lineno) ]
        except IndentationError, e:
            return [ ("Indentation Error", e.text.rstrip(), e.lineno) ]
        except TypeError, e:
            return [ ("Type Error", "Source contains NULL bytes", None) ]
        except Exception, e:
            return [ ("Unknown Error", str(e), None) ]

        return []

#-----------------------------------------------------------------------------#
class SyntaxCheckWindow(wx.Panel):
    __syntaxCheckers = {
        synextreg.ID_LANG_PYTHON: PythonSyntaxChecker,
        synextreg.ID_LANG_PHP: PhpSyntaxChecker
    }

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        ed_msg.Subscribe(self.OnFileSaved, ed_msg.EDMSG_FILE_SAVED)
        self._log = wx.GetApp().GetLog()
        vbox = wx.BoxSizer(wx.VERTICAL)
        self._listCtrl = wx.ListCtrl(
            self, style=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_SORT_ASCENDING
        )
        vbox.Add(self._listCtrl, 1, wx.EXPAND|wx.ALL)

        self._listCtrl.InsertColumn(0, _("Type"))
        self._listCtrl.InsertColumn(1, _("Error"))
        self._listCtrl.InsertColumn(2, _("File"))
        self._listCtrl.InsertColumn(3, _("Line"))
        self.SetSizer(vbox)
        self.SetAutoLayout(True)

    def __del__(self):
        ed_msg.Unsubscribe(self.OnFileSaved, ed_msg.EDMSG_FILE_SAVED)

    def OnFileSaved(self, arg):
        (fileName, fileType) = arg.GetData()
        util.Log("[SyntaxCheckWindow][info] fileName %s" % (fileName))
        try:
            syntaxChecker = self.__syntaxCheckers[fileType]
        except Exception, e:
            util.Log("[SyntaxCheckWindow][info] Error while checking %s: %s" % (fileName, str(e)))
            return

        data = syntaxChecker.Check(fileName)
        fD = FreezeDrawer(self._listCtrl)
        self._listCtrl.DeleteAllItems()

        if (len(data) == 0):
            return

        index = 0
        for (eType, eText, eLine) in data:
            self._listCtrl.InsertStringItem(index, str(eType))
            self._listCtrl.SetStringItem(index, 1, str(eText))
            self._listCtrl.SetStringItem(index, 2, fileName)
            self._listCtrl.SetStringItem(index, 3, str(eLine))
            index += 1
        self._listCtrl.SetColumnWidth(0, -1)
        self._listCtrl.SetColumnWidth(1, -1)
        self._listCtrl.SetColumnWidth(2, -1)
        self._listCtrl.SetColumnWidth(3, -1)

#-----------------------------------------------------------------------------#
# Implementation
class SyntaxCheck(plugin.Plugin):
    """Script Launcher and output viewer"""
    plugin.Implements(iface.ShelfI)
    ID_SYNTAXCHECK = wx.NewId()
    INSTALLED = False
    SHELF = None

    @property
    def __name__(self):
        return u'SyntaxCheck'

    def AllowMultiple(self):
        """Launch allows multiple instances"""
        return True

    def CreateItem(self, parent):
        """Create a Launch panel"""
        util.Log("[Launch][info] Creating SyntaxCheck instance for Shelf")
        return SyntaxCheckWindow(parent)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_BIN_FILE), wx.ART_MENU)
        return bmp

    def GetId(self):
        """The unique identifier of this plugin"""
        return self.ID_SYNTAXCHECK

    def GetMenuEntry(self, menu):
        """This plugins menu entry"""
        item = wx.MenuItem(menu, self.ID_SYNTAXCHECK, self.__name__,
                           _("Show syntax checker"))
        item.SetBitmap(self.GetBitmap())
        return item

    def GetMinVersion(self):
        return "4.39"

    def GetName(self):
        """The name of this plugin"""
        return self.__name__

    def InstallComponents(self, mainw):
        """Install extra menu components
        param mainw: MainWindow Instance

        """
        pass

    def IsInstalled(self):
        """Check whether launch has been installed yet or not
        @note: overridden from Plugin
        @return bool

        """
        return SyntaxCheck.INSTALLED

    def IsStockable(self):
        return True

#-----------------------------------------------------------------------------#
