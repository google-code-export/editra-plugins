#!/usr/bin/env python
############################################################################
#    Copyright (C) 2007 Cody Precord                                       #
#    cprecord@editra.org                                                   #
#                                                                          #
#    Editra is free software; you can redistribute it and#or modify        #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    Editra is distributed in the hope that it will be useful,             #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

"""
#--------------------------------------------------------------------------#
# FILE: HistWin.py
# AUTHOR: Cody Precord
# LANGUAGE: Python
# SUMMARY:
#
#
# METHODS:
#
#
#
#--------------------------------------------------------------------------#
"""

__author__ = "Cody Precord <cprecord@editra.org>"
__cvsid__ = "$Id$"
__revision__ = "$Revision$"

#--------------------------------------------------------------------------#
# Dependancies
import wx
import sys
import wx.lib.mixins.listctrl as listmix

_ = wx.GetTranslation
#--------------------------------------------------------------------------#
class HistoryWindow(wx.Frame):
    """Window for displaying the Revision History of a file"""
    def __init__(self, parent, title, data):
        wx.Frame.__init__(self, parent, title=title, style=wx.DEFAULT_DIALOG_STYLE)
        
        # Attributes
        self._ctrls = HistoryPane(self, data)

        # Layout
        self._DoLayout()
        self.SetInitialSize()

        # Event Handlers


    def _DoLayout(self):
        """Layout the controls"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self._ctrls, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)

#-----------------------------------------------------------------------------#

class HistoryPane(wx.Panel):
    """Panel for housing the the history window controls"""
    BTN_LBL1 = _("Compare to Previous")
    BTN_LBL2 = _("Compare Selected Versions")
    def __init__(self, parent, data):
        wx.Panel.__init__(self, parent)
        
        # Attributes
        self._search = LogSearch(self)
        self._split = wx.SplitterWindow(self, style=wx.SP_3DSASH | wx.SP_LIVE_UPDATE)
        self._list = HistList(self._split, data)
        self._txt = wx.TextCtrl(self._split, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self._btn = wx.Button(self, label=_(self.BTN_LBL1))

        # Layout
        self._DoLayout()
        self._txt.SetFocus()

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnButton, self._btn)

    def _DoLayout(self):
        """Layout the controls on the panel"""
        sizer = wx.GridBagSizer(5, 2)

        # Split Window
        self._split.SetMinimumPaneSize(50)
        self._split.SetMinSize((400, 300))
        self._split.SetSashSize(8)
        self._split.SplitHorizontally(self._list, self._txt, 250)

        sizer.AddMany([((5, 5), (0, 0)), # Spacer
                       (self._search, (1, 1), (1, 4), wx.EXPAND), # Search Control
                       (self._split, (2, 1), (10, 10), wx.EXPAND), # Split Window
                       ((5, 5), (11, 11)), # Spacer
                       (self._btn, (12, 10), (1, 1)), # Button
                       ((2, 2), (13, 0))]) # Spacer
        self.SetSizer(sizer)
        self.SetAutoLayout(True)

    def OnButton(self, evt):
        """Handle button events"""
        e_obj = evt.GetEventObject()
        lbl = e_obj.GetLabel()
        
        if lbl == self.BTN_LBL1:
            print "Diff to previous"
        else:
            print "Diff selected"

#-----------------------------------------------------------------------------#

class HistList(wx.ListCtrl, 
               listmix.ListCtrlAutoWidthMixin):
    """List for displaying a files revision history"""
    REV_COL = 0
    DATE_COL = 1
    AUTH_COL = 2
    COM_COL = 3
    def __init__(self, parent, data):
        wx.ListCtrl.__init__(self, parent,
                             style=wx.LC_REPORT | wx.LC_SORT_ASCENDING | \
                                   wx.LC_VRULES)

        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.InsertColumn(self.REV_COL, _("Rev #"))
        self.InsertColumn(self.DATE_COL, _("Date"))
        self.InsertColumn(self.AUTH_COL, _("Author"))
        self.InsertColumn(self.COM_COL, _("Log Message"))
        self.Populate(data)
#         self.SetColumnWidth(self.REV_COL, wx.LIST_AUTOSIZE)
#         self.SetColumnWidth(self.AUTH_COL, wx.LIST_AUTOSIZE)
#         self.SetColumnWidth(self.DATE_COL, wx.LIST_AUTOSIZE)
        self.SetColumnWidth(self.COM_COL, wx.LIST_AUTOSIZE)
        self.SendSizeEvent()

    def Populate(self, data):
        """Populate the list with the history data"""
        for item in data:
            index = self.InsertStringItem(sys.maxint, item['revision'])
            self.SetStringItem(index, 1, item['date'])
            self.SetStringItem(index, 2, item['author'])
            self.SetStringItem(index, 3, item['log'].strip())
            if not index % 2:
                syscolor = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DLIGHT)
#                 color = util.AdjustColour(syscolor, 75)
                self.SetItemBackgroundColour(index, syscolor)

#-----------------------------------------------------------------------------#

class LogSearch(wx.SearchCtrl):
    """Control for filtering history entries by searching log data"""
    def __init__(self, parent, value="", \
                 pos=wx.DefaultPosition, size=wx.DefaultSize, \
                 style=wx.TE_PROCESS_ENTER | wx.TE_RICH2):
        """Initializes the Search Control

        """
        wx.SearchCtrl.__init__(self, parent, wx.ID_ANY, value, pos, size, style)
        
        # Attributes

        # Appearance
        self.SetDescriptiveText(_("Search Log"))

        # Event Handlers
        # HACK, needed on Windows to get key events
        if wx.Platform == '__WXMSW__':
            self.ShowCancelButton(False)
            for child in self.GetChildren():
                if isinstance(child, wx.TextCtrl):
                    child.Bind(wx.EVT_KEY_UP, self.ProcessEvent)
                    break
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        self.Bind(wx.EVT_KEY_UP, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)

    def OnCancel(self, evt):
        """Clear the search"""
        self.SetValue(u"")
        self.ShowCancelButton(False)
        evt.Skip()

    def OnSearch(self, evt):
        """Search logs and filter"""
        print "searching..."

#-----------------------------------------------------------------------------#

if __name__ == '__main__':
    data = [
        {'revision':'a', 'date':'2007/17/01', 'author':'Kevin Smith', 'log':'Just Testing'},
    ]
    app = wx.PySimpleApp(False)
    win = HistoryWindow(None, "History Window Test", data)
    win.Show()
    app.MainLoop()

