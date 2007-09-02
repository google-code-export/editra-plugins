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
import re
import sys
import wx.lib.mixins.listctrl as listmix

# Editra Library Imports
try:
    import util
except ImportError:
    util = None

_ = wx.GetTranslation
#--------------------------------------------------------------------------#

edEVT_UPDATE_ITEMS = wx.NewEventType()
EVT_UPDATE_ITEMS = wx.PyEventBinder(edEVT_UPDATE_ITEMS, 1)
class UpdateItemsEvent(wx.PyCommandEvent):
    """Event to signal that items need updating"""
    def __init__(self, etype, eid, value=[]):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._etype = etype
        self._id = eid
        self._value = value

    def GetEvtType(self):
        return self._etype

    def GetId(self):
        return self._id

    def GetValue(self):
        return self._value

#--------------------------------------------------------------------------#

SB_INFO = 0
SB_PROG = 1
class HistoryWindow(wx.Frame):
    """Window for displaying the Revision History of a file"""
    def __init__(self, parent, title, projects, node, path):
        wx.Frame.__init__(self, parent, title=title, style=wx.DEFAULT_DIALOG_STYLE)
        
        # Set Frame Icon
        if util is not None:
            util.SetWindowIcon(self)

        # Attributes
        self._sb = HistoryStatusBar(self)
        self.SetStatusBar(self._sb)
        self._ctrls = HistoryPane(self, projects, node, path)

        # Layout
        self._DoLayout()
        self.SetInitialSize()

        # Event Handlers
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def _DoLayout(self):
        """Layout the controls"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self._ctrls, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def OnClose(self, evt):
        """Cleanup on exit"""
        self._sb.Destroy()
        self.Destroy()

    def Show(self, show=True):
        """Show and center the dialog"""
        self.CenterOnScreen()
        wx.Frame.Show(self, show)

    def StartBusy(self):
        """Start the window as busy"""
        self.SetStatusText(_("Retrieving File History") + u"...", SB_INFO)
        self._sb.StartBusy()

    def StopBusy(self):
        """Start the window as busy"""
        self.SetStatusText(u"", SB_INFO)
        self._sb.StopBusy()

#-----------------------------------------------------------------------------#

class HistoryStatusBar(wx.StatusBar):
    """Custom status bar for history window to show when its busy"""
    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent)
  
        # Attributes
        self._changed = False
        self.timer = wx.Timer(self)
        self.prog = wx.Gauge(self, style=wx.GA_HORIZONTAL)
        self.prog.Hide()

        # Layout
        self.SetFieldsCount(2)
        self.SetStatusWidths([-1, 125])

        # Event Handlers
        self.Bind(wx.EVT_TIMER, self.OnTick)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)

    def __del__(self):
        """Make sure the timer is stopped"""
        if self.timer.IsRunning():
            self.timer.Stop()

    def Destroy(self):
        """Cleanup timer"""
        if self.timer.IsRunning():
            self.timer.Stop()
        del self.timer
        wx.StatusBar.Destroy(self)

    def OnIdle(self, evt):
        """Reposition progress bar as necessary on moves, ect..."""
        if self._changed:
            self.Reposition()
        evt.Skip()

    def OnSize(self, evt):
        """Reposition progress bar on resize"""
        self.Reposition()
        self._changed = True
        evt.Skip()

    def OnTick(self, evt):
        """Update progress bar"""
        self.prog.Pulse()

    def Reposition(self):
        rect = self.GetFieldRect(1)
        self.prog.SetPosition((rect.x+2, rect.y+2))
        self.prog.SetSize((rect.width-4, rect.height-4))
        self._changed = False

    def StartBusy(self):
        """Start the timer"""
        self.prog.Show()
        self.timer.Start(100)

    def StopBusy(self):
        """Stop the timer"""
        self.prog.Hide()
        self.timer.Stop()

#-----------------------------------------------------------------------------#

class HistoryPane(wx.Panel):
    """Panel for housing the the history window controls"""
    BTN_LBL1 = _("Compare to Previous Revision")
    BTN_LBL2 = _("Compare to Selected Revision")
    BTN_LBL3 = _(" Compare Selected Revisions ")
    def __init__(self, parent, projects, node, path):
        wx.Panel.__init__(self, parent)
        
        # Attributes
        sbox = wx.StaticBox(self, label=_("Revision History"))
        # ?wxBug? If the box/sizer is created after the controls the controls
        #         that are added to the box cannot get focus from mouse clicks
        self.boxsz = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        self._search = LogSearch(self, size=(150, -1))
        self._split = wx.SplitterWindow(self, style=wx.SP_3DSASH | wx.SP_LIVE_UPDATE)
        self._list = HistList(self._split, projects, node, path)
        self._txt = wx.TextCtrl(self._split, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self._btn = wx.Button(self, label=_(self.BTN_LBL1))
        self.projects = projects
        self.path = path
        self.selected = -1

        # Layout
        self._DoLayout()
        self._txt.SetFocus()

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnButton, self._btn)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)

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
        self.GetParent().StartBusy()
        self._btn.Enable(False)
        selected = self.getSelectedItems()
        if not selected:
            self.projects.compareRevisions(self.path, callback=self.endCompare)
        elif len(selected) == 1:
            rev = self._list.GetItem(selected[0], self._list.REV_COL).GetText().strip()
            self.projects.compareRevisions(self.path, rev1=rev, callback=self.endCompare)
        else:
            rev1 = self._list.GetItem(selected[0], self._list.REV_COL).GetText().strip()
            rev2 = self._list.GetItem(selected[-1], self._list.REV_COL).GetText().strip()
            self.projects.compareRevisions(self.path, rev1=rev1, rev2=rev2, callback=self.endCompare)

    def endCompare(self):
        self._btn.Enable(True)
        self.GetParent().StopBusy()

    def getSelectedItems(self):
        item = -1
        selected = []
        while True:
            item = self._list.GetNextItem(item, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if item == -1:
                break
            selected.append(item)
        return selected
        
    def selectOnly(self, indices):
        """ Select only the given indices """
        item = -1
        while True:
            item = self._list.GetNextItem(item, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if item == -1:
                break
            if item not in indices:
                self._list.SetItemState(item, 0, wx.LIST_STATE_SELECTED)
                    
    def OnItemSelected(self, evt):
        """Update text control when an item is selected in the
        list control.

        """
        index = evt.GetIndex()
        rev = self._list.GetItem(index, self._list.REV_COL).GetText()
        date = self._list.GetItem(index, self._list.DATE_COL).GetText()
        self._txt.SetValue(self._list.GetFullLog(rev, date))
        self.updateButton()
        self.selectOnly((index,self.selected))
        self.selected = index

    def OnItemDeselected(self, evt):
        """Update text control when an item is selected in the
        list control.

        """
        selected = self.getSelectedItems()
        if not(selected):
            self.selected = -1
        elif len(selected) == 1:
            self.selected = selected[0]
        self.updateButton()
        
    def updateButton(self):
        selected = self.getSelectedItems()
        if not selected:
            self._btn.SetLabel(self.BTN_LBL1)
        elif len(selected) == 1:
            self._btn.SetLabel(self.BTN_LBL2)
        else:
            self._btn.SetLabel(self.BTN_LBL3)               

#-----------------------------------------------------------------------------#

class HistList(wx.ListCtrl, 
               listmix.ListCtrlAutoWidthMixin):
    """List for displaying a files revision history"""
    REV_COL = 0
    DATE_COL = 1
    AUTH_COL = 2
    COM_COL = 3
    def __init__(self, parent, projects, node, path):
        wx.ListCtrl.__init__(self, parent,
                             style=wx.LC_REPORT | wx.LC_SORT_ASCENDING | \
                                   wx.LC_VRULES)

        listmix.ListCtrlAutoWidthMixin.__init__(self)

        # Attributes
        self._frame = parent.GetGrandParent()
        self._data = {}

        self.Bind(EVT_UPDATE_ITEMS, self.OnUpdateItems)

        # Setup columns
        self.InsertColumn(self.REV_COL, _("Rev #"))
        self.InsertColumn(self.DATE_COL, _("Date"))
        self.InsertColumn(self.AUTH_COL, _("Author"))
        self.InsertColumn(self.COM_COL, _("Log Message"))
        wx.CallAfter(self._frame.StartBusy)
        projects.scCommand([node], 'history', callback=self.Populate)
        self.SetColumnWidth(self.COM_COL, wx.LIST_AUTOSIZE)
        self.SendSizeEvent()

    def OnUpdateItems(self, evt):
        index = -1
        append = False
        self.Freeze()
        for item in evt.GetValue():
            # Shorten log message for list item
            if 'shortlog' not in item:
                item['shortlog'] = log = item['log'].strip()
                if len(log) > 45:
                    log = log[:45] + u'...'
                    item['shortlog'] = log

            # Create a key for searching all fields
            if 'key' not in item:
                item['key'] = ('%s %s %s %s' % (item['revision'],
                                               item['date'],
                                               item['author'],
                                               re.sub(r'\s+', ' ', item['log']))).lower()

            if append:
                index = self.InsertStringItem(sys.maxint, '')
            else:
                index = self.GetNextItem(index)
                if index == -1:
                    append = True
                    index = self.InsertStringItem(sys.maxint, '')
            
            if self.GetItemText(index).strip() != item['revision']:
                self.SetStringItem(index, 0, item['revision'])
                self.SetStringItem(index, 1, item['date'])
                self.SetStringItem(index, 2, item['author'])
                self.SetStringItem(index, 3, item['shortlog'])

            if index % 2:
                syscolor = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DLIGHT)
                color = AdjustColour(syscolor, 75)
                self.SetItemBackgroundColour(index, color)

        # We never got to append mode, delete the extras
        if not append:
            for i in range(self.GetItemCount()-1, index, -1):
                self.DeleteItem(i)

        self.Thaw()
                
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
        if not data:
            wx.MessageDialog(self, 
               _('The history information for the requested file could ' \
                 'not be retrieved.  Please make sure that you have network access.'), 
               _('History information could not be retrieved'), 
               style=wx.OK|wx.ICON_ERROR).ShowModal()
            self.GetGrandParent().GetParent().Destroy()
            return
        evt = UpdateItemsEvent(edEVT_UPDATE_ITEMS, self.GetId(), data)
        wx.PostEvent(self, evt)                                
        wx.CallAfter(self._frame.StopBusy)

    def Filter(self, query):
        query = [x for x in query.strip().lower().split() if x]
        if query:
            newdata = []
            for item in self._data:
                i = 0
                for word in query:
                    if word in item['key']:
                        i += 1
                if i == len(query):
                    newdata.append(item)
        else:
            newdata = self._data
        evt = UpdateItemsEvent(edEVT_UPDATE_ITEMS, self.GetId(), newdata)
        wx.PostEvent(self, evt)                                

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
        self.GetParent()._list.Filter(self.GetValue())

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

