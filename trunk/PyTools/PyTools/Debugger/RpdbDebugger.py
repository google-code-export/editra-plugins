# -*- coding: utf-8 -*-
# Name: RpdbDebugger.py
# Purpose: Debug Client
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" RpdbDebugger functions """

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
from time import sleep

# Editra Libraries
import util

# Local Imports
import rpdb2
from PyTools.Debugger.RpdbStateManager import RpdbStateManager
from PyTools.Debugger.RpdbBreakpointsManager import RpdbBreakpointsManager
from PyTools.Debugger.RpdbStackFrameManager import RpdbStackFrameManager
from PyTools.Debugger.RpdbThreadsManager import RpdbThreadsManager
from PyTools.Debugger.RpdbVariablesManager import RpdbVariablesManager

#----------------------------------------------------------------------------#

class RpdbDebugger(object):
    fAllowUnencrypted = True
    fRemote = False
    host = "localhost"
    fAttach = True
    fchdir = False
    password = "editra123"

    def __init__(self):
        super(RpdbDebugger, self).__init__()
        self.sessionmanager = rpdb2.CSessionManager(RpdbDebugger.password, \
            RpdbDebugger.fAllowUnencrypted, RpdbDebugger.fRemote, RpdbDebugger.host)
        self.breakpointmanager = RpdbBreakpointsManager(self)
        self.statemanager = RpdbStateManager(self)
        self.stackframemanager = RpdbStackFrameManager(self)
        self.threadmanager = RpdbThreadsManager(self)
        self.variablesmanager = RpdbVariablesManager(self)
        
        # attributes that will be set later
        self.mainwindowid = None
        self._config = {}
        self.pid = None
        self.breakpoints = {}
        self.breakpoints_loaded = False
        self.curstack = {}
        self.unhandledexception = False
        
        # functions that will be set later

        # message handler
        self.conflictingmodules = lambda x:None
        self.setstepmarker = lambda x,y:None        
        self.clearstepmarker = lambda:None
        self.setstepmarker = lambda x,y:None
        self.restorestepmarker = lambda x:None      
        # debuggee shelf
        self.debuggeroutput = lambda x:None
        self.abort = lambda:None
        # breakpoints shelf
        self.saveandrestorebreakpoints = lambda:None
        # stackframe shelf
        self.clearframe = lambda:None
        self.selectframe = lambda x:None
        self.updatestacklist = lambda x:None
        # thread shelf
        self.clearthread = lambda:None
        self.updatethread = lambda x,y,z:None
        self.updatethreadlist = lambda x,y:None
        # variables shelf
        self.clearlocalvariables = lambda:None
        self.clearglobalvariables = lambda:None
        self.clearexceptions = lambda:None
        self.updatelocalvariables = lambda x,y:(None,None)
        self.updateglobalvariables = lambda x,y:(None,None)
        self.updateexceptions = lambda x,y:(None,None)
        self.catchunhandledexception = lambda:None
        # expressions shelf
        self.restoreexpressions = lambda:None
        self.saveandrestoreexpressions = lambda:None
        self.clearexpressionvalues = lambda:None

    def clear_all(self):
        self.pid = None
        self.breakpoints_loaded = False
        self.curstack = {}
        self.unhandledexception = False
        self.abort = lambda:None
        self.clearstepmarker()
        self.clearframe()
        self.clearthread()
        self.clearlocalvariables()
        self.clearglobalvariables()
        self.clearexceptions()
        self.clearexpressionvalues()

    def isrpdbbreakpoint(self, filepath, lineno):
        if filepath.find("rpdb2.py") == -1:
            return False
        bpinfile = self.breakpoints.get(filepath)
        if not bpinfile:
            return True
        if not bpinfile.get(lineno):
            return True
        return False

    def attach(self, abortfn):
        if self.pid:
            tries = 0
            err = None
            while tries != 5:
                sleep(1)
                util.Log("[PyDbg][info] Trying to Attach")
                err = None
                try:
                    self.sessionmanager.attach(self.pid, encoding = rpdb2.detect_locale())
                    break
                except Exception, err:
                    tries = tries + 1
            self.pid = None
            if err:
                util.Log("[PyDbg][err] Failed to attach. Error: %s" % repr(err))
                abortfn()
                return
            self.abort = abortfn
            util.Log("[PyDbg][info] Running")

    def do_detach(self):
        try:
            self.sessionmanager.detach()
        except rpdb2.NotAttached:
            pass

    def register_callback(self, func, event_type_dict, fSingleUse = False):
        self.sessionmanager.register_callback(func, event_type_dict, fSingleUse = fSingleUse)

    def load_breakpoints(self):
        self.breakpointmanager.loadbreakpoints()
            
    def set_frameindex(self, index):
        try:
            self.sessionmanager.set_frame_index(index)        
        except rpdb2.NotAttached:
            pass
            
    def get_frameindex(self):
        try:
            return self.sessionmanager.get_frame_index()        
        except rpdb2.NotAttached:
            pass
        return None
    
    def update_stack(self):
        try:
            stacklist = self.sessionmanager.get_stack([], True)        
            self.stackframemanager.do_update_stack(stacklist[0])
        except rpdb2.NotAttached:
            pass

    def get_thread_list(self):
        try:
            return self.sessionmanager.get_thread_list()        
        except rpdb2.NotAttached:
            pass
        return (None, {})
    
    def set_thread(self, tid):
        try:
            self.sessionmanager.set_thread(tid)        
        except rpdb2.NotAttached:
            pass
            
    def execute(self, suite):
        try:
            return self.sessionmanager.execute(suite)
        except rpdb2.NotAttached:
            return None

    def evaluate(self, suite):
        try:
            return self.sessionmanager.evaluate(suite)
        except rpdb2.NotAttached:
            return None

    def update_namespace(self):
        self.variablesmanager.update_namespace()

    def get_namespace(self, expressionlist, filterlevel):
        try:
            return self.sessionmanager.get_namespace(expressionlist, filterlevel)
        except rpdb2.NotAttached:
            return None

    def set_analyze(self, analyze):
        try:
            self.sessionmanager.set_analyze(analyze)   
        except rpdb2.NotAttached:
            pass
            
    def do_stop(self):
        try:
            self.sessionmanager.stop_debuggee()
            self.clearstepmarker()
        except rpdb2.NotAttached:
            pass

    def do_restart(self):
        try:
            self.sessionmanager.restart()
            self.clearstepmarker()
        except rpdb2.NotAttached:
            pass

    def do_jump(self, lineno):
        try:
            self.sessionmanager.request_jump(lineno)
            self.clearstepmarker()
        except rpdb2.NotAttached:
            pass

    def do_go(self):
        try:
            self.sessionmanager.request_go()
            self.clearstepmarker()
        except rpdb2.NotAttached:
            pass

    def do_break(self):
        try:
            self.sessionmanager.request_break()
        except rpdb2.NotAttached:
            pass

    def do_step(self):
        try:
            self.sessionmanager.request_step()
            self.clearstepmarker()
        except rpdb2.NotAttached:
            pass

    def do_next(self):
        try:
            self.sessionmanager.request_next()
            self.clearstepmarker()
        except rpdb2.NotAttached:
            pass

    def do_return(self):
        try:
            self.sessionmanager.request_return()
            self.clearstepmarker()
        except rpdb2.NotAttached:
            pass

    def run_toline(self, filename, lineno):
        try:
            self.sessionmanager.request_go_breakpoint(filename, '', lineno)
            self.clearstepmarker()
        except rpdb2.NotAttached:
            pass

    def disable_breakpoint(self, bpid):
        try:
            self.sessionmanager.disable_breakpoint([bpid], True)
        except rpdb2.NotAttached:
            pass

    def enable_breakpoint(self, bpid):
        try:
            self.sessionmanager.enable_breakpoint([bpid], True)
        except rpdb2.NotAttached:
            pass

    def clear_breakpoints(self):
        try:
            self.sessionmanager.load_breakpoints()
        except:
            pass
        try:
            self.sessionmanager.delete_breakpoint([], True)
            self.sessionmanager.save_breakpoints()
        except rpdb2.NotAttached:
            pass
        
    def set_breakpoint(self, filepath, lineno, exprstr = "", enabled=True):
        try:
            return self.sessionmanager.set_breakpoint(filepath, '', lineno, enabled, exprstr)
        except rpdb2.NotAttached:
            return None

    def delete_breakpoint(self, bpid):
        try:
            self.sessionmanager.delete_breakpoint([bpid], True)
        except rpdb2.NotAttached:
            pass
