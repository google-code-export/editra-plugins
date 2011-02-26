# -*- coding: utf-8 -*-
# Name: RpdbStateManager.py
# Purpose: Debug State
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" RpdbStateManager functions """

__version__ = "0.2"
__author__ = "Mike Rans"
__svnid__ = "$Id: RpdbStateManager.py 1025 2010-12-24 18:30:23Z rans@email.com $"
__revision__ = "$Revision: 1025 $"

#-----------------------------------------------------------------------------#
# Imports
import sys
import os.path
import wx

# Editra Libraries
import ed_msg

# Local Imports
import rpdb2

class RpdbStateManager(object):
    def __init__(self, sessionmanager, breakpointmanager):
        super(RpdbStateManager, self).__init__()
        self.m_state = rpdb2.STATE_DETACHED
        self.sessionmanager = sessionmanager
        self.breakpointmanager = breakpointmanager
        state = self.sessionmanager.get_state()
        self.update_state(rpdb2.CEventState(state))
        self.mwid = None
        
        event_type_dict = {rpdb2.CEventState: {}}
        self.sessionmanager.register_callback(self.update_state, event_type_dict, fSingleUse = False)

    def set_mainwindowid(self, mwid):
        self.mwid = mwid
    
    def update_state(self, event):
        wx.CallAfter(self.callback_state, event)

    def callback_state(self, event):
        old_state = self.m_state
        self.m_state = event.m_state

        # change menu or toolbar items displayed according to state eg. running, paused etc.

        if self.m_state == rpdb2.STATE_DETACHED:
            # clear all debugging stuff as we have finished
            if self.mwid:
                ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_STATE, (self.mwid, 0, 0))
                self.mwid = None
        elif (old_state in [rpdb2.STATE_DETACHED, rpdb2.STATE_DETACHING, rpdb2.STATE_SPAWNING, rpdb2.STATE_ATTACHING]) and (self.m_state not in [rpdb2.STATE_DETACHED, rpdb2.STATE_DETACHING, rpdb2.STATE_SPAWNING, rpdb2.STATE_ATTACHING]):
            try:
                serverinfo = self.sessionmanager.get_server_info()
                # we are debugging serverinfo.m_filename
                f = self.sessionmanager.get_encryption()
                ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_STATE, (self.mwid, -1, -1))
            except rpdb2.NotAttached:
                pass

        if self.m_state == rpdb2.STATE_BROKEN:
            # we hit a breakpoint
            # show the stack viewer, threads viewer, namespace viewer
            state_text = rpdb2.STR_STATE_BROKEN
            if not self.breakpointmanager.breakpoints_set:
                wx.CallAfter(self.breakpointmanager.loadbreakpoints)
        elif self.m_state == rpdb2.STATE_ANALYZE:
            # we are analyzing an exception
            # show the stack viewer and namespace viewer
            pass
        else:
            # any other state
            # don't show any viewers
            pass
