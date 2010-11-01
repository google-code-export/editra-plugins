# -*- coding: utf-8 -*-
# Name: CheckResultsList.py                                                   
# Purpose: Pylint plugin                                              
# Author: Mike Rans                              
# Copyright: (c) 2010 Mike Rans                                
# License: wxWindows License                                                  
###############################################################################

"""Editra Shelf display window"""

__version__ = "0.2"
__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

import wx
import wx.lib.mixins.listctrl as mixins
from wx.stc import STC_INDIC_SQUIGGLE, STC_INDIC2_MASK
import eclib.elistmix as elistmix
_ = wx.GetTranslation

class CheckResultsList(wx.ListCtrl,
                       mixins.ListCtrlAutoWidthMixin,
                       elistmix.ListRowHighlighter):
    """List control for displaying syntax check results"""
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        mixins.ListCtrlAutoWidthMixin.__init__(self)
        elistmix.ListRowHighlighter.__init__(self)

        # Attributes
        self._charWidth = self.GetCharWidth()

        # Setup
        self.InsertColumn(0, _("Type"))
        self.InsertColumn(1, _("Line"))
        self.InsertColumn(2, _("Error"))
        # Auto-resize col

        self.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)

        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivate)
        self.editor = None
        self.errorlines = {}

    def set_mainwindow(self, mw):
        self._mainw = mw
        
    def set_editor(self, editor):
        self.editor = editor

    def OnItemActivate(self, evt):
        """Go to the error in the file"""
        if not self.editor:
            return
        idx = evt.GetIndex()
        itm = self.GetItem(idx, 1).GetText()
        try:
            lineNo = int(itm)
            self.editor.GotoLine(max(0, lineNo - 1))
        except ValueError:
            pass

    def DeleteOldRows(self):
        """Delete all the rows """
        if not self.editor:
            return
        for itemIndex in reversed(xrange(0, self.GetItemCount())):
            self.DeleteItem(itemIndex)
        CheckResultsList.unset_indic(self.editor)
        self.errorlines = {}
        
    def PopulateRows(self, data):
        """Populate the list with the data
        @param data: list of tuples (errorType, errorText, errorLine)

        """
        if not self.editor:
            return
        self.editor.IndicatorSetStyle(2, STC_INDIC_SQUIGGLE)
        self.editor.IndicatorSetForeground(2, 'red')
        
        typeText = _("Type")
        errorText = _("Error")
        minLType = max(self.GetTextExtent(typeText)[0], self.GetColumnWidth(0))
        minLText = max(self.GetTextExtent(errorText)[0], self.GetColumnWidth(2))
        self.errorlines = {}
        for (eType, eText, eLine) in data:
            minLType = max(minLType, self.GetTextExtent(eType)[0])
            minLText = max(minLText, self.GetTextExtent(eText)[0])
            #For some reason a simple Append() does not seem to work...
            lineNo = self.GetItemCount()
            lineNo = self.InsertStringItem(lineNo, unicode(eType))
            for (col, txt) in [ (1, unicode(eLine)), (2, unicode(eText)) ]:
                self.SetStringItem(lineNo, col, txt)
            try:
                lineNo = int(eLine)
                if CheckResultsList.set_indic(lineNo - 1, eType, self.editor):
                    self.errorlines[lineNo] = eText
            except ValueError:
                pass
        self.SetColumnWidth(0, minLType)
        self.SetColumnWidth(2, minLText)

    def show_calltip(self, lineno):
        if not self.editor:
            return
        if lineno in self.errorlines:
            self.editor.CallTipShow(lineno, self.errorlines[lineno])
        else:
            self.editor.CallTipCancel()
        
    @staticmethod
    def set_indic(lineNo, eType, editor):
        """Highlight a word by setting an indicator
        
        @param start: number of a symbol where the indicator starts
        @type start: int
        
        @param length: length of the highlighted word
        @type length: int
        """

        if eType != "Error":
            return False
        
        start = editor.PositionFromLine(lineNo)
        text = editor.GetLineUTF8(lineNo)
        editor.StartStyling(start, STC_INDIC2_MASK)
        editor.SetStyling(len(text), STC_INDIC2_MASK)
        return True

    @staticmethod
    def unset_indic(editor):
        """Remove all the indicators"""
        if not editor:
            return
        editor.StartStyling(0, STC_INDIC2_MASK)
        end = editor.GetTextLength()
        editor.SetStyling(end, 0)

    @staticmethod
    def _printListCtrl(ctrl):
        for row in xrange(0, ctrl.GetItemCount()):
            for column in xrange(0, ctrl.GetColumnCount()):
                print ctrl.GetItem(row, column).GetText(), "\t",
            print ""
