# -*- coding: utf-8 -*-
# Name: ExpressionDialog.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra expression dialog"""

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#----------------------------------------------------------------------------#
# Imports
import os.path
import wx

# Editra Libraries
import eclib

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class ExpressionDialog(eclib.ECBaseDlg):
    def __init__(self, parent, default_value):
        super(ExpressionDialog, self).__init__(parent, wx.ID_ANY, "Enter Expression")    
        
        label = wx.StaticText(self, -1, \
        "The new expression will be evaluated at the debuggee and its value will be set to the item.")
        self._sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        sizerh = wx.BoxSizer(wx.HORIZONTAL)
        self._sizer.Add(sizerh, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        label = wx.StaticText(self, -1, "New Expression:")
        sizerh.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        self.m_entry_expr = wx.TextCtrl(self, value = default_value, size = (200, -1))
        self.m_entry_expr.SetFocus()
        self.Bind(wx.EVT_TEXT, self.OnText, self.m_entry_expr)
        sizerh.Add(self.m_entry_expr, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        btnsizer = wx.StdDialogButtonSizer()
        self._sizer.Add(btnsizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        
        self.m_ok = wx.Button(self, wx.ID_OK)
        self.m_ok.SetDefault()
        self.m_ok.Disable()
        btnsizer.AddButton(self.m_ok)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        self._sizer.Fit(self)        

    def OnText(self, event):
        if event.GetString() == '':
            self.m_ok.Disable()
        else:
            self.m_ok.Enable()

        event.Skip()
                   
    def get_expression(self):
        expr = self.m_entry_expr.GetValue()
        return unicode(expr)
