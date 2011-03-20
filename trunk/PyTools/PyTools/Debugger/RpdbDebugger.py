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
from PyTools.Common.PyToolsUtils import PyToolsUtils
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
        self.attached = False
        self.mainwindow = None
        self._config = {}
        self.pid = None
        self.breakpoints = {}
        self.breakpoints_installed = False
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
        self.breakpoints_installed = False
        self.curstack = {}
        self.unhandledexception = False
        self.attached = False
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
            ex = None
            while tries != 5:
                sleep(1)
                util.Log("[PyDbg][info] Trying to Attach")
                ex = None
                try:
                    self.sessionmanager.attach(self.pid, encoding = rpdb2.detect_locale())
                    break
                except Exception, ex:
                    tries = tries + 1
            self.pid = None
            if ex:
                err = rpdb2.g_error_mapping.get(type(ex), repr(ex))
                err = "Failed to attach. Error: %s" % err
                util.Log("[PyDbg][err] %s" % err)
                self.debuggeroutput("\n%s" % err)
                PyToolsUtils.error_dialog(self.mainwindow, err)
                self.attached = False
                abortfn()
                return
            self.abort = abortfn
            self.attached = True
            util.Log("[PyDbg][info] Running")

    def callsessionmanagerfn(self, fn, *args, **kwargs):
        ex = None
        try:
            return fn(*args, **kwargs)
        except rpdb2.NotAttached, ex:
            if not self.attached:
                return None
            self.attached = False
        except Exception, ex:
            pass
        if self.mainwindow:
            err = rpdb2.g_error_mapping.get(type(ex), repr(ex))
            PyToolsUtils.error_dialog(self.mainwindow, err)
        return None
    
    def do_detach(self):
        self.callsessionmanagerfn(self.sessionmanager.detach)

    def register_callback(self, func, event_type_dict, fSingleUse = False):
        self.sessionmanager.register_callback(func, event_type_dict, fSingleUse = fSingleUse)

    def install_breakpoints(self):
        self.breakpointmanager.installbreakpoints()
            
    def set_frameindex(self, index):
        self.callsessionmanagerfn(self.sessionmanager.set_frame_index, index)
            
    def get_frameindex(self):
        return self.callsessionmanagerfn(self.sessionmanager.get_frame_index)
    
    def update_stack(self):
        stacklist = self.callsessionmanagerfn(self.sessionmanager.get_stack, [], True)
        if stacklist is not None:
            self.stackframemanager.do_update_stack(stacklist[0])

    def get_thread_list(self):
        res = self.callsessionmanagerfn(self.sessionmanager.get_thread_list)
        if res is not None:
            return res
        return (None, {})
    
    def set_thread(self, tid):
        self.callsessionmanagerfn(self.sessionmanager.set_thread, tid)
            
    def execute(self, suite):
        return self.callsessionmanagerfn(self.sessionmanager.execute, suite)

    def evaluate(self, suite):
        return self.callsessionmanagerfn(self.sessionmanager.evaluate, suite)

    def update_namespace(self):
        self.variablesmanager.update_namespace()

    def get_namespace(self, expressionlist, filterlevel):
        return self.callsessionmanagerfn(self.sessionmanager.get_namespace, expressionlist, filterlevel)

    def set_analyze(self, analyze):
        self.callsessionmanagerfn(self.sessionmanager.set_analyze, analyze)
            
    def do_stop(self):
        self.callsessionmanagerfn(self.sessionmanager.stop_debuggee)
        self.clearstepmarker()

    def do_restart(self):
        self.callsessionmanagerfn(self.sessionmanager.restart)
        self.clearstepmarker()

    def do_jump(self, lineno):
        self.callsessionmanagerfn(self.sessionmanager.request_jump, lineno)
        self.clearstepmarker()

    def do_go(self):
        self.callsessionmanagerfn(self.sessionmanager.request_go)
        self.clearstepmarker()

    def do_break(self):
        self.callsessionmanagerfn(self.sessionmanager.request_break)

    def do_step(self):
        self.callsessionmanagerfn(self.sessionmanager.request_step)
        self.clearstepmarker()

    def do_next(self):
        self.callsessionmanagerfn(self.sessionmanager.request_next)
        self.clearstepmarker()

    def do_return(self):
        self.callsessionmanagerfn(self.sessionmanager.request_return)
        self.clearstepmarker()

    def run_toline(self, filename, lineno):
        self.callsessionmanagerfn(self.sessionmanager.request_go_breakpoint, filename, '', lineno)
        self.clearstepmarker()

    def disable_breakpoint(self, bpid):
        self.callsessionmanagerfn(self.sessionmanager.disable_breakpoint, [bpid], False)

    def enable_breakpoint(self, bpid):
        self.callsessionmanagerfn(self.sessionmanager.enable_breakpoint, [bpid], False)

    def load_breakpoints(self):
        try:
            self.sessionmanager.load_breakpoints()
        except rpdb2.NotAttached:
            pass
        except IOError:
            pass
    
    def clear_breakpoints(self):
        self.callsessionmanagerfn(self.sessionmanager.delete_breakpoint, [], True)
        
    def set_breakpoint(self, filepath, lineno, exprstr = "", enabled=True):
        return self.callsessionmanagerfn(self.sessionmanager.set_breakpoint, filepath, '', lineno, enabled, exprstr)

    def get_breakpoints(self):
        return self.callsessionmanagerfn(self.sessionmanager.get_breakpoints)

    def delete_breakpoint(self, filepath, lineno):
        bps = self.get_breakpoints()
        if not bps:
            return
        for bp in bps.values():            
            if bp.m_lineno == lineno and bp.m_filename == filepath:
                self.callsessionmanagerfn(self.sessionmanager.delete_breakpoint, [bp.m_id], False)
