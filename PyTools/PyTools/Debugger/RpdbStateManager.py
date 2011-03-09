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
import wx

# Editra Libraries
import ed_msg

# Local Imports
import rpdb2

#----------------------------------------------------------------------------#

class RpdbStateManager(object):
    def __init__(self, rpdb2debugger):
        super(RpdbStateManager, self).__init__()
        self.m_state = rpdb2.STATE_DETACHED
        self.rpdb2debugger = rpdb2debugger
        state = self.rpdb2debugger.sessionmanager.get_state()
        self.update_state(rpdb2.CEventState(state))
        
        event_type_dict = {rpdb2.CEventState: {}}
        self.rpdb2debugger.register_callback(self.update_state, event_type_dict)

    def update_state(self, event):
        wx.CallAfter(self.callback_state, event)

    def callback_state(self, event):
        old_state = self.m_state
        self.m_state = event.m_state

        # change menu or toolbar items displayed according to state eg. running, paused etc.
        if self.m_state == rpdb2.STATE_DETACHED:
            if self.rpdb2debugger.breakpoints_loaded:
                # clear all debugging stuff as we have finished
                ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (self.rpdb2debugger.mainwindowid, False))
                wx.CallAfter(self.rpdb2debugger.clear_all)
        elif (old_state in [rpdb2.STATE_DETACHED, rpdb2.STATE_DETACHING, rpdb2.STATE_SPAWNING, rpdb2.STATE_ATTACHING]) and (self.m_state not in [rpdb2.STATE_DETACHED, rpdb2.STATE_DETACHING, rpdb2.STATE_SPAWNING, rpdb2.STATE_ATTACHING]):
            try:
                serverinfo = self.rpdb2debugger.sessionmanager.get_server_info()
                # we are debugging serverinfo.m_filename
                f = self.rpdb2debugger.sessionmanager.get_encryption()
                ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_STATE, (self.rpdb2debugger.mainwindowid, -1, -1))
            except rpdb2.NotAttached:
                pass

        if self.m_state == rpdb2.STATE_BROKEN:
            # we hit a breakpoint
            # show the stack viewer, threads viewer, namespace viewer
            pass
            
        elif self.m_state == rpdb2.STATE_ANALYZE:
            # we are analyzing an exception
            # show the stack viewer and namespace viewer
            pass
        else:
            # any other state
            # don't show any viewers
            pass
