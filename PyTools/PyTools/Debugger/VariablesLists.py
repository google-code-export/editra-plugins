# -*- coding: utf-8 -*-
# Name: VariablesList.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id: VariablesList.py -1   $"
__revision__ = "$Revision: -1 $"

#----------------------------------------------------------------------------#
# Imports
import os.path
import threading
import wx
import wx.gizmos

# Editra Libraries
import eclib

# Local Imports
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Debugger.ExpressionDialog import ExpressionDialog
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation
STR_NAMESPACE_DEADLOCK = "Data Retrieval Timeout"
STR_NAMESPACE_LOADING = "Loading..."
STR_MAX_NAMESPACE_WARNING_TITLE = "Namespace Warning"

#----------------------------------------------------------------------------#

class VariablesList(wx.gizmos.TreeListCtrl):
    """List control for displaying stack frame results"""
    def __init__(self, parent, listtype, filterlevel):
        super(VariablesList, self).__init__(parent)

        # Setup
        self.AddColumn(_("Name"))
        self.AddColumn(_("Repr"))
        self.AddColumn(_("Type"))
        self.SetMainColumn(0) 
        self.SetLineSpacing(0)
        
        # Attributes
        self.listtype = listtype
        self.filterlevel = filterlevel
        self.ignoredwarnings = {'': True}
        
        # Event Handlers
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnItemExpanding)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSING, self.OnItemCollapsing)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_TREE_ITEM_GETTOOLTIP, self.OnItemToolTip)
            
    def set_mainwindow(self, mw):
        self._mainw = mw

    def Clear(self):
        """Delete all the rows """
        self.DeleteAllItems()

    def PopulateRows(self, data):
        """Populate the list with the data
        @param data: dictionary of variables info

        """
        root = self.AddRoot("root")
        self.SetItemPyData(root, (self.listtype, False))
        self.SetItemHasChildren(root, True)

        variablelist = [root]

        while len(variablelist) > 0:
            item = variablelist.pop(0)
            self.expand_item(item, data, item is root)
            
            items = self.get_children(item)
            variablelist = items + variablelist

    def OnItemToolTip(self, event):
        item = event.GetItem()

        tooltip = self.GetItemText(item, 2)[1:]
        event.SetToolTip(tooltip)
       
    def OnItemCollapsing(self, event):
        item = event.GetItem()

        event.Skip()

    def OnItemActivated(self, event):
        item = event.GetItem()
        (expr, is_valid) = self.GetPyData(item)
        if expr in [STR_NAMESPACE_LOADING, STR_NAMESPACE_DEADLOCK, STR_MAX_NAMESPACE_WARNING_TITLE]:
            return
        wx.CallAfter(self._onitemactivated, item, expr, is_valid)
        
    def _onitemactivated(self, item, expr, is_valid):
        if is_valid:
            default_value = self.GetItemText(item, 2)[1:]
        else:
            default_value = ""

        expr_dialog = ExpressionDialog(self, default_value)
        pos = self.GetPositionTuple()
        expr_dialog.SetPosition((pos[0] + 50, pos[1] + 50))
        r = expr_dialog.ShowModal()
        if r != wx.ID_OK:
            expr_dialog.Destroy()
            return

        _expr = expr_dialog.get_expression()

        expr_dialog.Destroy()

        _suite = "%s = %s" % (expr, _expr)

        res = None
        exc_info = (None, None, None)
        
        res = RPDBDEBUGGER.execute(_suite)        
        if not res:
            return
            
        warning, error = res
        
        if error != '':
            dlg = wx.MessageDialog(self, error, "Error", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        if not warning in self.ignoredwarnings:
            dlg = wx.MessageDialog(self, "%s\n\nClick 'Cancel' to ignore this warning in this session." % warning,\
            "Warning", wx.OK | wx.CANCEL | wx.YES_DEFAULT | wx.ICON_WARNING)
            res = dlg.ShowModal()
            dlg.Destroy()

            if res == wx.ID_CANCEL:
                self.ignoredwarnings[warning] = True
                
    def OnItemExpanding(self, event):
        item = event.GetItem()        

        if not self.ItemHasChildren(item):
            event.Skip()
            return
        
        if self.get_numberofchildren(item) > 0:
            event.Skip()
            self.Refresh();
            return
        
        wx.CallAfter(self._onitemexpanding, item)
    
    def _onitemexpanding(self, item):
        self.DeleteChildren(item)
        
        child = self.AppendItem(item, STR_NAMESPACE_LOADING)
        self.SetItemText(child, ' ' + STR_NAMESPACE_LOADING, 2)
        self.SetItemText(child, ' ' + STR_NAMESPACE_LOADING, 1)
        self.SetItemPyData(child, (STR_NAMESPACE_LOADING, False))

        (expr, is_valid) = self.GetPyData(item)

        item = self.find_item(expr)
        if item == None:
            return
      
        variables = RPDBDEBUGGER.get_namespace([(expr, True)], self.filterlevel)

        if not variables:
            child = self.AppendItem(item, STR_NAMESPACE_DEADLOCK)
            self.SetItemText(child, ' ' + STR_NAMESPACE_DEADLOCK, 2)
            self.SetItemText(child, ' ' + STR_NAMESPACE_DEADLOCK, 1)
            self.SetItemPyData(child, (STR_NAMESPACE_DEADLOCK, False))
            self.Expand(item)

            if freselect_child:
                self.SelectItem(child)

            return
        #
        # When expanding a tree item with arrow-keys on wxPython 2.6, the 
        # temporary "loading" child is automatically selected. After 
        # replacement with real children we need to reselect the first child.
        #
        children = self.get_children(item)
        freselect_child = len(children) != 0 and children[0] == self.GetSelection()
            
        self.DeleteChildren(item)
                
        self.expand_item(item, variables, False, True)  

        if freselect_child:
            children = self.get_children(item)
            self.SelectItem(children[0])

        self.Refresh()
        
    # Helper functions
    def get_numberofchildren(self, item):
        nochildren = self.GetChildrenCount(item)
        if nochildren != 1:
            return nochildren 

        child = self.get_children(item)[0]
        (expr, is_valid) = self.GetPyData(child)

        if expr in [STR_NAMESPACE_LOADING, STR_NAMESPACE_DEADLOCK]:
            return 0

        return 1

    def expand_item(self, item, variables, froot = False, fskip_expansion_check = False):
        if not self.ItemHasChildren(item):
            return
        
        if not froot and not fskip_expansion_check and self.IsExpanded(item):
            return

        if self.get_numberofchildren(item) > 0:
            return
        
        (expr, is_valid) = self.GetPyData(item)

        variables_with_expr = [e for e in variables if e.get("expr", None) == expr]
        if variables_with_expr == []:
            return

        first_variable_with_expr = variables_with_expr[0] 
        if first_variable_with_expr is None:
            return   

        if "error" in first_variable_with_expr:
            return
        
        if first_variable_with_expr["n_subnodes"] == 0:
            self.SetItemHasChildren(item, False)
            return

        #
        # Create a list of the subitems.
        # The list is indexed by name or directory key.
        # In case of a list, no sorting is needed.
        #

        for subnode in first_variable_with_expr["subnodes"]:
            _name = unicode(subnode["name"])
            _type = unicode(subnode["type"])
            _repr = unicode(subnode["repr"])

            child = self.AppendItem(item, _name)
            self.SetItemText(child, ' ' + _repr, 2)
            self.SetItemText(child, ' ' + _type, 1)
            self.SetItemPyData(child, (subnode["expr"], subnode["fvalid"]))
            self.SetItemHasChildren(child, (subnode["n_subnodes"] > 0))

        self.Expand(item)

    def find_item(self, expr):
        item = self.GetRootItem()
        while item:
            (expr2, is_valid) = self.GetPyData(item)
            if expr2 == expr:
                return item               
                
            item = self.GetNext(item)

        return None    
    
    def get_children(self, item):
        (child, cookie) = self.GetFirstChild(item)
        children = []
        
        while child and child.IsOk():
            children.append(child)
            (child, cookie) = self.GetNextChild(item, cookie)

        return children    

    def get_expression_list(self):
        if self.GetCount() == 0:
            return None

        item = self.GetRootItem()

        variablelist = [item]
        expressionlist = []

        while len(variablelist) > 0:
            item = variablelist.pop(0)
            (expr, is_valid) = self.GetPyData(item)
            fExpand = self.IsExpanded(item) and self.get_numberofchildren(item) > 0
            if not fExpand:
                continue

            expressionlist.append((expr, True))
            items = self.get_children(item)
            variablelist = items + variablelist

        return expressionlist    

