#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#Name: cbrowser.py                                                           #
#Purpose: UI portion of the CommentBrowser Plugin                            #
#Author: DR0ID <dr0iddr0id@googlemail.com>                                   #
#Copyright: (c) 2008 DR0ID                                                   #
#Licence: wxWindows Licence                                                  #
###############################################################################

"""
Provides a comment browser panel and other UI components for Editra's
CommentBrowser Plugin.

"""

__author__ = 'DR0ID <dr0iddr0id@googlemail.com>'
__svnid__ = '$Id: browser.py 50827 2007-12-19 08:48:03Z CJP $'
__revision__ = '$Revision$'

#-----------------------------------------------------------------------------#
#Imports
import sys
import wx
import wx.lib.mixins.listctrl as listmix

#Editra Library Modules
import ed_glob
#import ed_menu

#--------------------------------------------------------------------------#
#Globals
_ = wx.GetTranslation

PANE_NAME = u'CommentBrowser'
CAPTION = _(u'Comment Browser')
ID_CBROWSERPANE = wx.NewId()
ID_COMMENTBROWSE = wx.NewId()

#--------------------------------------------------------------------------#


class CBrowserPane(wx.Panel):

    """Creates a Commentbrowser panel"""

    def __init__(
        self,
        parent,
        id,
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.NO_BORDER,
        ):
        """ Initializes the CBrowserPane class"""

        wx.Panel.__init__(
            self,
            parent,
            id,
            pos,
            size,
            style,
            )

        self._mainwin = parent
        self.__log = wx.GetApp().GetLog()

        #---- Add Menu Items ----#
        viewm = self._mainwin.GetMenuBar().GetMenuByName('view')
        self._mi = viewm.InsertAlpha(ID_COMMENTBROWSE, CAPTION,
                _('Open Comment Browser Sidepanel'), wx.ITEM_CHECK,
                after=ed_glob.ID_PRE_MARK)
        self._mainwin.Bind(wx.aui.EVT_AUI_PANE_CLOSE, self.OnClose)
        #TODO: update if gets focus?
        #TODO: update every second?
        #TODO: update when tab changes (should every tab have its own todo list??)
        #TODO: two tabs, one for current file, one for all opened files??
        #columns: (priority, comment, file, linenr)

        #XXX: testing
        ID_listctrl = wx.NewId()
        self._listctrl = TestListCtrl(self, ID_listctrl)
        
        

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._listctrl, 1, wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Layout()

    def _log(self, msg):
        """writes a log message to the app log"""

        self.__log('[commentbrowser] ' + str(msg))

    def OnShow(self, evt):
        """Shows the Comment Browser"""

        self._log('OnShow')
        if evt.GetId() == ID_COMMENTBROWSE:
            mgr = self._mainwin.GetFrameManager()
            pane = mgr.GetPane(PANE_NAME)
            if pane.IsShown():
                pane.Hide()
                self._mi.Check(False)
            else:
#               Profile_Set('SHOW_FB', False)
                pane.Show()
                self._mi.Check(True)
#               Profile_Set('SHOW_FB', True)
            mgr.Update()
        else:
            evt.Skip()

    def OnClose(self, evt):
        """Clean up settings when Comment Browser is closed"""

        evt_caption = evt.GetPane().caption
        if CAPTION == evt_caption:
            self._log('OnClose ')
            self._mi.Check(False)
            evt.Skip()



#---------------------------------------------------------------------------- #


class TestListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin,
            listmix.ColumnSorterMixin):

    """The list ctrl used for the list"""

    def __init__(
        self,
        parent,
        ID,
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.BORDER_NONE|wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.LC_SINGLE_SEL):
        """Init the list ctrl"""

        self._log('TestListCtrl before init base classes')
        wx.ListCtrl.__init__(
            self,
            parent,
            ID,
            pos,
            size,
            style,
            )
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self._log('TestListCtrl after init base classes')


        #---- Images used by the list ----#
        isize = (8, 8)
        self._img_list = wx.ImageList(*isize)
        self.sm_up = \
            self._img_list.Add(wx.ArtProvider_GetBitmap(wx.ART_GO_UP,
                               wx.ART_TOOLBAR, isize))
        self.sm_dn = \
            self._img_list.Add(wx.ArtProvider_GetBitmap(wx.ART_GO_DOWN,
                               wx.ART_TOOLBAR, isize))
        self.SetImageList(self._img_list, wx.IMAGE_LIST_SMALL)

        #this attribute ist required by listmix.ColumnSorterMixin
        #{1:(col1, col2, col3), etc.}
        self.itemDataMap = dict()
        self.itemIndexMap = []

        #---- Add Columns Headers ----#

        self.InsertColumn(0, "!")
        self.InsertColumn(1, "Description")
        self.InsertColumn(2, "File")
        self.InsertColumn(3, "Line")

        self.SetColumnWidth(0, 38)
        self.SetColumnWidth(1, 454)
        self.SetColumnWidth(2, 149)
        self.SetColumnWidth(3, 63)

        self._log('after adding columns')
        
        #TODO: remove testentries
        self.AddEntry(4, 'The Price Of Love', 'file', '23')
        self.AddEntry('1', 'bla bla bla', 'file', '25')
        self.AddEntry('5', 'Love python', 'file', '4')

        self._log('after adding entries')
        
        # hast to be after self.itemDataMap has been initialized and the
        # setup of the columns, but befor sorting
        listmix.ColumnSorterMixin.__init__(self, 4)

        #---- Events ----#
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected,
                  self)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated,
                  self)
        self.Bind(wx.EVT_LIST_DELETE_ITEM, self.OnItemDelete, self)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self)
        self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnColRightClick,
                  self)
        self.Bind(wx.EVT_LIST_COL_BEGIN_DRAG, self.OnColBeginDrag, self)
        self.Bind(wx.EVT_LIST_COL_DRAGGING, self.OnColDragging, self)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.OnColEndDrag, self)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginEdit, self)

        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)

        #for wxMSW
        self.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)

        #for wxGTK
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)

        self._log('after binding events')


        #sort by genre (column 0), A->Z ascending order (1)
        self.SortListItems(0, 0)

        self._log('__init__() finished')
        
    

    def _log(self, msg):
        wx.GetApp().GetLog()('>>>>>>>>>>>>>>[commentbrowser][listctr] '
                              + str(msg))

    def AddEntry(
        self,
        prio,
        descr,
        file,
        line,
        ):
        # add to itemDataMap for sorting
        prio = str(prio)
        descr = str(descr)
        file = str(file)
        line = str(line)
        key = len(self.itemDataMap)
        self.itemDataMap[key] = (prio, descr, file, line)
        self.itemIndexMap = list(self.itemDataMap.keys())
        # add to actual list
        index = self.InsertStringItem(sys.maxint, prio)
        self.SetStringItem(index, 1, descr)
        self.SetStringItem(index, 2, file)
        self.SetStringItem(index, 3, line)
        # this is really needed by the ColumnSorterMixin
        self.SetItemData(index, key)
        self._log("itemcount Add entry "+str(self.GetItemCount()))
#         self.SetItemCount(self.GetItemCount())
#         self.SetItemCount(key)
        self.Refresh()
        #FIXME: remove debug
        self._log(self.itemDataMap)


    # These methods are callbacks for implementing the
    # "virtualness" of the list...

    def OnGetItemText(self, item, col):
        index=self.itemIndexMap[item]
        s = self.itemDataMap[index][col]
        return s

    def OnGetItemImage(self, item):
        return -1

    def OnGetItemAttr(self, item):
        return None




    #Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        """ this method is required by listmix.ColumnSorterMixin"""

        self._log('GetListCtrl')
        return self

    #---------------------------------------------------
    #Matt C, 2006/02/22
    #Here's a better SortItems() method --
    #the ColumnSorterMixin.__ColumnSorter() method already handles the ascending/descending,
    #and it knows to sort on another column if the chosen columns have the same value.
    def SortItems(self, sorter=cmp):
        self._log('SortItems')
        items = list(self.itemDataMap.keys())
        self._log(items)
        items.sort(sorter)
        self._log(items)
        self.itemIndexMap = items

        #redraw the list
        self.Refresh()
        
    #Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetSortImages(self):
        self._log('GetSortImages')
        return (self.sm_dn, self.sm_up)

    #---- Eventhandler ----#

    def OnItemSelected(self, event):
        self._log('OnItemSelected')
        self.currentItem = event.m_itemIndex
        self._log("OnItemSelected: %s, %s, %s, %s, %s\n" %
                           (self.currentItem,
                            self.GetItem(self.currentItem, 0).GetText(),
                            self.GetItem(self.currentItem, 1).GetText(),
                            self.GetItem(self.currentItem, 2).GetText(),
                            self.GetItem(self.currentItem, 3).GetText()))
        event.Skip()

    def OnItemDeselected(self, event):
        self._log('OnItemDeselected')
        item = event.GetItem()
        self._log("OnItemDeselected: %d" % event.m_itemIndex)

    def OnItemActivated(self, event):
        self._log('OnItemActivated')

    def OnItemDelete(self, event):
        self._log('OnItemDelete')

    def OnColClick(self, event):
        self._log('OnColClick')
        event.Skip()

    def OnColRightClick(self, event):
        self._log('OnColRightClick')

    def OnColBeginDrag(self, event):
        self._log('OnColBeginDrag')

    def OnColDragging(self, event):
        self._log('OnColDragging')

    def OnColEndDrag(self, event):
        self._log('OnColEndDrag')
        for colnum in [0, 1, 2, 3]:
            self._log(self.GetColumnWidth(colnum))

    def OnBeginEdit(self, event):
        self._log('OnBeginEdit')

    def OnDoubleClick(self, event):
        self._log('OnDoubleClick')

    def OnRightDown(self, event):
        self._log('OnRightDown')

    def OnRightClick(self, event):
        self._log('OnRightClick')


