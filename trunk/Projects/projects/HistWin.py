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
    def __init__(self, parent, title, projects):
        wx.Frame.__init__(self, parent, title=title, style=wx.DEFAULT_DIALOG_STYLE)
        
        # Attributes
        self._ctrls = HistoryPane(self, projects)

        # Layout
        self._DoLayout()
        self.SetInitialSize()

        # Event Handlers


    def _DoLayout(self):
        """Layout the controls"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self._ctrls, 1, wx.EXPAND)
        self.SetSizer(sizer)

#-----------------------------------------------------------------------------#

class HistoryPane(wx.Panel):
    """Panel for housing the the history window controls"""
    BTN_LBL1 = _("Compare to Previous")
    BTN_LBL2 = _("Compare Selected Versions")
    def __init__(self, parent, projects):
        wx.Panel.__init__(self, parent)
        
        # Attributes
        sbox = wx.StaticBox(self, label=_("Revision History"))
        # ?wxBug? If the box/sizer is created after the controls the controls
        #         that are added to the box cannot get focus from mouse clicks
        self.boxsz = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        self._search = LogSearch(self, size=(150, -1))
        self._split = wx.SplitterWindow(self, style=wx.SP_3DSASH | wx.SP_LIVE_UPDATE)
        self._list = HistList(self._split, projects)
        self._txt = wx.TextCtrl(self._split, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self._btn = wx.Button(self, label=_(self.BTN_LBL1))

        # Layout
        self._DoLayout()
        self._txt.SetFocus()

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnButton, self._btn)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)

    def _DoLayout(self):
        """Layout the controls on the panel"""
        sizer = wx.GridBagSizer(5, 2)

        # Split Window
        self._split.SetMinimumPaneSize(50)
        self._split.SetMinSize((400, 300))
        self._split.SetSashSize(8)
        self._split.SplitHorizontally(self._list, self._txt, 250)
        self.boxsz.Add(self._search, 0, wx.ALIGN_RIGHT)
        self.boxsz.Add((10, 10))
        self.boxsz.Add(self._split, 1, wx.EXPAND)

        sizer.AddMany([((5, 5), (0, 0)), # Spacer
                       (self.boxsz, (1, 1), (10, 10), wx.EXPAND), # Split Window
                       ((5, 5), (10, 11)), # Spacer
                       (self._btn, (11, 10), (1, 1)), # Button
                       ((2, 2), (12, 0))]) # Spacer
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

    def OnItemSelected(self, evt):
        """Update text control when an item is selected in the
        list control.

        """
        index = evt.GetIndex()
        rev = self._list.GetItem(index, self._list.REV_COL).GetText()
        date = self._list.GetItem(index, self._list.DATE_COL).GetText()
        self._txt.SetValue(self._list.GetFullLog(rev, date))

#-----------------------------------------------------------------------------#

class HistList(wx.ListCtrl, 
               listmix.ListCtrlAutoWidthMixin):
    """List for displaying a files revision history"""
    REV_COL = 0
    DATE_COL = 1
    AUTH_COL = 2
    COM_COL = 3
    def __init__(self, parent, projects):
        wx.ListCtrl.__init__(self, parent,
                             style=wx.LC_REPORT | wx.LC_SORT_ASCENDING | \
                                   wx.LC_VRULES)

        listmix.ListCtrlAutoWidthMixin.__init__(self)

        # Setup columns
        self.InsertColumn(self.REV_COL, _("Rev #"))
        self.InsertColumn(self.DATE_COL, _("Date"))
        self.InsertColumn(self.AUTH_COL, _("Author"))
        self.InsertColumn(self.COM_COL, _("Log Message"))
        projects.scCommand([projects.getSelectedNodes()[0]], 'history', 
                                    callback=self.Populate)
        self.SetColumnWidth(self.COM_COL, wx.LIST_AUTOSIZE)
        self.SendSizeEvent()

    def GetFullLog(self, rev, timestamp):
        """Get the full log entry for the given revision"""
        for item in self._data:
            if item['revision'] == rev and item['date'] == timestamp:
                return item['log']
        else:
            return wx.EmptyString

    def Populate(self, data):
        """Populate the list with the history data"""
        self._data = data
        for item in data:
            index = self.InsertStringItem(sys.maxint, item['revision'])
            self.SetStringItem(index, 1, item['date'])
            self.SetStringItem(index, 2, item['author'])

            log = item['log'].strip()
            if len(log) > 45:
                log = log[:45] + u'...'
            self.SetStringItem(index, 3, log)
            if index % 2:
                syscolor = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DLIGHT)
                color = AdjustColour(syscolor, 75)
                self.SetItemBackgroundColour(index, color)

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
# Helper functions
def AdjustColour(color, percent, alpha=wx.ALPHA_OPAQUE):
    """ Brighten/Darken input colour by percent and adjust alpha
    channel if needed. Returns the modified color.
    @param color: color object to adjust
    @type color: wx.Color
    @param percent: percent to adjust +(brighten) or -(darken)
    @type percent: int
    @keyword alpha: amount to adjust alpha channel

    """ 
    end_color = wx.WHITE
    rdif = end_color.Red() - color.Red()
    gdif = end_color.Green() - color.Green()
    bdif = end_color.Blue() - color.Blue()
    high = 100

    # We take the percent way of the color from color -. white
    red = color.Red() + ((percent * rdif * 100) / high) / 100
    green = color.Green() + ((percent * gdif * 100) / high) / 100
    blue = color.Blue() + ((percent * bdif * 100) / high) / 100
    return wx.Colour(red, green, blue, alpha)
#-----------------------------------------------------------------------------#

if __name__ == '__main__':
    data = [
        {'revision':'a', 'date':'2007/17/01', 'author':'Kevin Smith', 'log':'Just Testing'},
        {'revision':'b', 'date':'2007/17/02', 'author':'Kevin Smith', 'log':'Test again with some longer text'},
        {'revision':'c', 'date':'2007/17/03', 'author':'Kevin Smith', 'log':'Just Testing'},
        {'revision':'d', 'date':'2007/17/04', 'author':'Kevin Smith', 'log':'Log message with lots of text to test the truncation of long messages and their display in the text control.'}
    ]
    app = wx.PySimpleApp(False)
    win = HistoryWindow(None, "History Window Test", data)
    win.Show()
    app.MainLoop()

