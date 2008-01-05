###############################################################################
# Name:  cbrowserlistctrl.py                                                  #
# Purpose: a simple to use listctrl for todo tasks                            #
# Author: DR0ID <dr0iddr0id@googlemail.com>                                   #
# Copyright: (c) 2007 DR0ID                                                   #
# Licence: wxWindows Licence                                                  #
###############################################################################

"""
Provides a virtual ListCtrl for the CommentBrowser
"""

__author__ = "DR0ID"
__svnid__ = "$Id: Exp $"
__revision__ = "$Revision$"

#------------------------------------------------------------------------------#
# Imports
import sys
import wx
import wx.lib.mixins.listctrl as listmix

#Editra Library Modules
import ed_glob

#------------------------------------------------------------------------------#
# Globals


_ = wx.GetTranslation

#------------------------------------------------------------------------------#



class TestListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin,
            listmix.ColumnSorterMixin):

    """The list ctrl used for the list"""

    def __init__(
        self,
        parent,
        ID=-1,
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.BORDER_NONE|wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.LC_SINGLE_SEL|wx.LC_VIRTUAL):
        """Init the TestListCtrl"""

        self._log('TestListCtrl before init base classes')
        wx.ListCtrl.__init__(
            self,
            parent,
            ID,
            pos,
            size,
            style,
            )

        #---- Images used by the list ----#
        isize = (8, 8)
        self._img_list = wx.ImageList(*isize)
        up = wx.ArtProvider_GetBitmap(str(ed_glob.ID_UP), wx.ART_MENU, isize)
        if not up.IsOk():
            up = wx.ArtProvider_GetBitmap(wx.ART_GO_UP, wx.ART_TOOLBAR, isize)
        self.sm_up = self._img_list.Add(up)

        down = wx.ArtProvider_GetBitmap(str(ed_glob.ID_DOWN), wx.ART_MENU, isize)
        if not down.IsOk():
            down = wx.ArtProvider_GetBitmap(wx.ART_GO_DOWN, wx.ART_TOOLBAR, isize)
        self.sm_dn = self._img_list.Add(down)

        self.SetImageList(self._img_list, wx.IMAGE_LIST_SMALL)

        #---- Add Columns Headers ----#
        self.InsertColumn(0, "!")
        self.InsertColumn(1, "Type")
        self.InsertColumn(2, "Description")
        self.InsertColumn(3, "File")
        self.InsertColumn(4, "Line")

        self.SetColumnWidth(0, 38)
        self.SetColumnWidth(1, 59)
        self.SetColumnWidth(2, 429)
        self.SetColumnWidth(3, 117)

        self._log('after adding columns')
        #---- data ----#
        #this attribute ist required by listmix.ColumnSorterMixin
        self.itemDataMap = {} #{1:(prio, task, description, file, line), etc.}
        self.itemIndexMap = self.itemDataMap.keys()
        self.SetItemCount(len(self.itemDataMap))
        self._currentItemIdx = -1
        
        #---- init base classes ----#
        # hast to be after self.itemDataMap has been initialized and the
        # setup of the columns, but befor sorting
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, 5)
        self._log('TestListCtrl after init base classes')

        #---- Events ----#
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected,
                  self)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnItemRightClick,
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

        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick, self)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown, self)

        #for wxMSW
        self.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick, self)

        #for wxGTK
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightClick, self)

        self._log('after binding events')

#         #TODO: remove testentries
#         self.AddEntry(4, 'TODO', 'The Price Of Love', 'file', '25')
#         self.AddEntry(4, 'TODO', 'The brice Of Love', 'file', '36')
#         self.AddEntry(4, 'TODO', 'The OOOH Of Love', 'file', '24')
#         self.AddEntry('1', 'FIXME', 'bla bla bla', 'file', '52')
#         self.AddEntry('2', 'FIXME', 'zla bla bla', 'file', '55')
#         self.AddEntry('3', 'FIXME', 'grr bla bla', 'file', '25')
#         self.AddEntry('5', 'XXX', 'Love python', 'file', '66')
#         self.AddEntry('2', 'XXX', 'Love love python', 'file', '404')
#         self.AddEntry('4', 'XXX', 'Love py', 'file', '44')
#         self._log('after adding entries')

        #sort by prio (column 0), descending order (0)
        self.SortListItems(0, 0)

        self._log('__init__() finished')
        
    #---- methods ----#

    def _log(self, msg):
        """Private log method of this class"""
        wx.GetApp().GetLog()('>>>>>>>>>>>>>>[commentbrowser][listctr] '
                              + str(msg))

    def AddEntry(
        self,
        prio,
        tasktype,
        descr,
        file,
        line,
        fullname,
        refresh = True
        ):
        """Add a entry to the list"""
        # add to itemDataMap for sorting
        val = (int(prio), str(tasktype), str(descr), str(file), int(line), str(fullname))
        key = hash(val)
        self.itemDataMap[key] = val
        # TODO: perhaps add it in a sorted manner (if possible, dont know)
        self.itemIndexMap = list(self.itemDataMap.keys())
        self.SetItemCount(len(self.itemDataMap))
        if refresh:
            self.Refresh()
        
        #FIXME: remove debug
        self._log("itemcount Add entry "+str(self.GetItemCount())+" key:"+str(key))
        
        return key
        
    def AddEntries(self, entrylist):
        """Adds all entries from the entrylist. The entries must be a tuple
        containing (prio, tasktype, description, file, line)"""
        keys = []
        for entry in entrylist:
            prio, task, descr, file, line , fullname = entry
            keys.append(self.AddEntry(prio, task, descr, file, line, fullname, refresh=False))
        self.SetItemCount(len(self.itemDataMap))
        self.Refresh()
        return keys
        
    def RemoveEntry(self, key):
        """Removes a entry identified by its key"""
        self.itemDataMap.pop(key, None)
        self.itemIndexMap = list(self.itemDataMap.keys())
        self.SetItemCount(len(self.itemDataMap))
        self.Refresh()
        
    def Clear(self, keys=None, refresh=True):
        """Removes all entries from list"""
        if keys is None:
            self.itemDataMap.clear()
            self.itemIndexMap = list(self.itemDataMap.keys())
            self.SetItemCount(len(self.itemDataMap))
            if refresh:
                self.Refresh()
        else:
            for key in keys:
                self.RemoveEntry(key)

    def NavigateToTaskSource(self, itemIndex):
    
        if itemIndex < 0 or itemIndex > len(self.itemDataMap):
            return
        
        key = self.itemIndexMap[itemIndex]
        source = str(self.itemDataMap[key][-1])
        line = self.itemDataMap[key][-2]
        try:
            nb = self.GetParent().GetParent().GetNotebook()
            ctrls = nb.GetTextControls()
            for ctrl in ctrls:
                if source == ctrl.GetFileName() :
                    nb.SetSelection(nb.GetPageIndex(ctrl))
                    nb.GoCurrentPage()
                    ctrl.GotoLine(line-1)
                    break;
        except Exception, e:
            self._log("[error] "+e.msg)


    #---- special methods used by the mixinx classes ----#
    
    #Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        """ this method is required by listmix.ColumnSorterMixin"""

#         self._log('GetListCtrl')
        return self

    #---------------------------------------------------
    #Matt C, 2006/02/22
    #Here's a better SortItems() method --
    #the ColumnSorterMixin.__ColumnSorter() method already handles the ascending/descending,
    #and it knows to sort on another column if the chosen columns have the same value.
    def SortItems(self, sorter=cmp):
        """This method is required by the 
        wx.lib.mixins.listctrl.ColumnSorterMixin, for internal usage only"""
        items = list(self.itemDataMap.keys())
        items.sort(sorter)
        self.itemIndexMap = items

        #redraw the list
        self.Refresh()
        
    #Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetSortImages(self):
        """
        This method is required by the 
        wx.lib.mixins.listctrl.ColumnSorterMixin, for internal usage only
        """
#         self._log('GetSortImages')
        return (self.sm_dn, self.sm_up)
        
    #---- special listctrl eventhandlers ----#
        # These methods are callbacks for implementing the
        # "virtualness" of the list...

    def OnGetItemText(self, item, col):
        """
        Virtual ListCtrl have to define this method, returns the text of the
        requested item
        """
#         s = ''
#         self._log("OnGetItemText")
#         self._log(self.GetItemCount())
#         if len(self.itemIndexMap):
        index = self.itemIndexMap[item]
        s = self.itemDataMap[index][col]
        return s

    def OnGetItemImage(self, item):
        """
        Virtual ListCtrl have to define this method, should return an image
        for the item, but since we have no images it always returns -1.
        """
        return -1

    def OnGetItemAttr(self, itemIdx):
        """
        Virtual ListCtrl have to define this method, should return item 
        attributes, but since we have none it always returns None.
        """
        return None

    #---- Eventhandler ----#
    
    #TODO: comment, remove

    def OnItemSelected(self, event):
        self._log('OnItemSelected')
        self._currentItemIdx = event.m_itemIndex
        self._log("OnItemSelected: %s, %s, %s, %s, %s\n" %
                           (self._currentItemIdx,
                            self.GetItem(self._currentItemIdx, 0).GetText(),
                            self.GetItem(self._currentItemIdx, 1).GetText(),
                            self.GetItem(self._currentItemIdx, 2).GetText(),
                            self.GetItem(self._currentItemIdx, 3).GetText()))
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
        self._log('OnDoubleClick'+str(event))
        # OnItemSelected is called first, so self._currentItemIdx is already set
        self.NavigateToTaskSource(self._currentItemIdx)
        

    def OnRightDown(self, event):
        self._log('OnRightDown')
        event.Skip()

    def OnRightClick(self, event):
        self._log('OnRightClick')
        event.Skip()

    def OnItemRightClick(self, event):
        self.NavigateToTaskSource(event.m_itemIndex)
        event.Skip()
        
    

