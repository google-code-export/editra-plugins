# -*- coding: utf-8 -*-
# Name: AttachDialog.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra attach dialog"""

__author__ = "Mike Rans"
__svnid__ = "$Id: AttachDialog.py 1142 2011-03-19 19:21:26Z rans@email.com $"
__revision__ = "$Revision: 1142 $"

#----------------------------------------------------------------------------#
# Imports
import sys
import wx

# Editra Libraries
import eclib

# Local imports
import rpdb2
from PyTools.Common.PyToolsUtils import RunProcInThread
from PyTools.Debugger import RPDBDEBUGGER
from PyTools.Debugger.PasswordDialog import PasswordDialog

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class AttachDialog(eclib.ECBaseDlg):
    def __init__(self, parent):
        super(AttachDialog, self).__init__(parent, wx.ID_ANY, "Attach")    
        
        # Attributes
        self.parent = parent
        self.m_server_list = None
        self.m_errors = {}
        self.m_index = None
        
        # Layout
        sizerv = wx.BoxSizer(wx.VERTICAL)

        desc = "Attach to a script (that has the debugger engine running) on local or remote machine:"
        label = wx.StaticText(self, -1, desc, size = (350, -1))
        try:
            label.Wrap(350)
        except:
            desc = """Attach to a script (that has the debugger engine 
running) on local or remote machine:"""
            label.SetLabel(desc)

        sizerv.Add(label, 0, wx.ALIGN_LEFT | wx.ALL, 5)

        sizerh = wx.BoxSizer(wx.HORIZONTAL)
        sizerv.Add(sizerh, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        label = wx.StaticText(self, -1, "Host:")
        sizerh.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        self.m_entry_host = wx.TextCtrl(self, value = self.parent._lasthost, size = (200, -1))
        self.m_entry_host.SetFocus()
        sizerh.Add(self.m_entry_host, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        btn = wx.Button(self, label = "Refresh")
        self.Bind(wx.EVT_BUTTON, self.do_refresh, btn) # for some reason, this must be up here otherwise window hangs
        btn.SetDefault()
        sizerh.Add(btn, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        self.m_listbox_scripts = eclib.EBaseListCtrl(parent = self, style = wx.LC_REPORT | wx.LC_SINGLE_SEL, size = (-1, 300))
        self.m_listbox_scripts.InsertColumn(0, "PID" + '    ')
        self.m_listbox_scripts.InsertColumn(1, "Filename")
        
        sizerv.Add(self.m_listbox_scripts, 0, wx.EXPAND | wx.ALL, 5)

        btnsizer = wx.StdDialogButtonSizer()
        sizerv.Add(btnsizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.m_ok = wx.Button(self, wx.ID_OK)
        self.m_ok.Disable()
        btnsizer.AddButton(self.m_ok)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        self.SetSizer(sizerv)
        sizerv.Fit(self)

        # Event Handlers
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.m_listbox_scripts)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected, self.m_listbox_scripts)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated, self.m_listbox_scripts)
        
        wx.CallAfter(self.init2)

    def init2(self):
        pwd_dialog = PasswordDialog(self, self.parent._lastpwd)
        pos = self.GetPositionTuple()
        pwd_dialog.SetPosition((pos[0] + 50, pos[1] + 50))
        r = pwd_dialog.ShowModal()
        if r != wx.ID_OK:
            pwd_dialog.Destroy()
            self.Close()
            return

        self.parent._lastpwd = pwd_dialog.get_password()
        pwd_dialog.Destroy()

        RPDBDEBUGGER.set_password(self.parent._lastpwd)            
        self.do_refresh()
                
    def set_cursor(self, id):
        cursor = wx.StockCursor(id)
        self.SetCursor(cursor)        
        self.m_listbox_scripts.SetCursor(cursor)        

    def OnCloseWindow(self, event):
        self.m_ok = None
        event.Skip()

    def get_server(self):
        return self.m_server_list[self.m_index]
        
    def do_refresh(self, event = None):
        host = self.m_entry_host.GetValue()
        if host == '':
            host = 'localhost'
        self.parent._lasthost = host
        worker = RunProcInThread("DbgAttach", self._onserverlist,
                                 RPDBDEBUGGER.get_server_list, host)
        worker.start()
        
    def _onserverlist(self, res):
        if not res or not self.m_ok:
            return
        (self.m_server_list, self.m_errors) = res
        
        if len(self.m_errors) > 0:
            for k, el in self.m_errors.items():
                if k in [rpdb2.AuthenticationBadData, rpdb2.AuthenticationFailure]:
                    self.report_attach_warning(rpdb2.STR_ACCESS_DENIED)

                elif k == rpdb2.EncryptionNotSupported:
                    self.report_attach_warning(rpdb2.STR_DEBUGGEE_NO_ENCRYPTION)
                    
                elif k == rpdb2.EncryptionExpected:
                    self.report_attach_warning(rpdb2.STR_ENCRYPTION_EXPECTED)

                elif k == rpdb2.BadVersion:
                    for (t, v, tb) in el:
                        self.report_attach_warning(rpdb2.STR_BAD_VERSION % {'value': v})
        
        self.m_ok.Disable()
            
        host = RPDBDEBUGGER.get_host()
        self.m_entry_host.SetValue(host)

        self.m_listbox_scripts.DeleteAllItems()

        for i, s in enumerate(self.m_server_list):
            index = self.m_listbox_scripts.InsertStringItem(sys.maxint, repr(s.m_pid))
            
            self.m_listbox_scripts.SetStringItem(index, 1, s.m_filename)
            self.m_listbox_scripts.SetItemData(index, i)

    def report_attach_warning(self, warning):
        dlg = wx.MessageDialog(self, warning, "Warning", wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()   

    def OnItemSelected(self, event):
        self.m_index = event.m_itemIndex
        self.m_ok.Enable()

        event.Skip()

    def OnItemDeselected(self, event):
        if self.m_listbox_scripts.GetSelectedItemCount() == 0:
            self.m_ok.Disable()

        event.Skip()    
        
    def OnItemActivated(self, event):
        self.m_index = event.m_itemIndex

        self.EndModal(wx.ID_OK)