# -*- coding: utf-8 -*-
# Name: PasswordDialog.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra password dialog"""

__author__ = "Mike Rans"
__svnid__ = "$Id: PasswordDialog.py 1191 2011-03-27 15:57:44Z rans@email.com $"
__revision__ = "$Revision: 1191 $"

#----------------------------------------------------------------------------#
# Imports
import wx

# Editra Libraries
import eclib

# Local imports
import rpdb2
from PyTools.Common.PyToolsUtils import PyToolsUtils

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class PasswordDialog(eclib.ECBaseDlg):
    def __init__(self, parent, current_password):
        super(PasswordDialog, self).__init__(parent, wx.ID_ANY, "Password")    
        
        # Layout
        sizerv = wx.BoxSizer(wx.VERTICAL)

        pwddesc = "The password is used to secure communication between the debugger console"
        pwddesc += "and the debuggee. Debuggees with un-matching passwords will not appear in the attach query list."
        label = wx.StaticText(self, -1, pwddesc, size = (300, -1))
        try:
            label.Wrap(300)
        except:
            pwddesc = """The password is used to secure communication 
between the debugger console and the debuggee. 
Debuggees with un-matching passwords will not 
appear in the attach query list."""
            label.SetLabel(pwddesc)

        sizerv.Add(label, 1, wx.ALIGN_LEFT | wx.ALL, 5)

        sizerh = wx.BoxSizer(wx.HORIZONTAL)
        sizerv.Add(sizerh, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        label = wx.StaticText(self, -1, "Set password:")
        sizerh.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        pwd = [current_password, ''][current_password is None]

        self.m_entry_pwd = wx.TextCtrl(self, value = pwd, size = (200, -1))
        self.m_entry_pwd.SetFocus()
        self.Bind(wx.EVT_TEXT, self.OnText, self.m_entry_pwd)
        sizerh.Add(self.m_entry_pwd, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        btnsizer = wx.StdDialogButtonSizer()
        sizerv.Add(btnsizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        
        self.m_ok = wx.Button(self, wx.ID_OK)
        self.m_ok.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.do_ok, self.m_ok)
        if pwd == '':
            self.m_ok.Disable()
        btnsizer.AddButton(self.m_ok)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        self.SetSizer(sizerv)
        sizerv.Fit(self)        

    def OnText(self, event):
        if event.GetString() == '':
            self.m_ok.Disable()
        else:
            self.m_ok.Enable()

        event.Skip()        
                   
    def get_password(self):
        pwd = self.m_entry_pwd.GetValue()
        return pwd

    def do_validate(self):
        if rpdb2.is_valid_pwd(self.get_password()):
            return True

        baddpwd = "The password should begin with a letter and continue with any combination of digits,"
        baddpwd += "letters or underscores (\'_\'). Only English characters are accepted for letters."
        PyToolsUtils.error_dialog(self, baddpwd)
        
        return False

    def do_ok(self, event):
        f = self.do_validate()
        if not f:
            return

        event.Skip()
