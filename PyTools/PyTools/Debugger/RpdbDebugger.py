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
import traceback
from time import sleep

# Editra Libraries
import util
from profiler import Profile_Get
import ed_msg

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
        self.analyzing = False
        self.mainwindow = None
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
        self.debugbuttonsupdate = lambda:None
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
        self.updateanalyze = lambda:None
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
        self.analyzing = False
        self.abort = lambda:None
        self.clearstepmarker()
        self.clearframe()
        self.clearthread()
        self.clearlocalvariables()
        self.clearglobalvariables()
        self.clearexceptions()
        self.clearexpressionvalues()
        self.saveandrestoreexpressions()
        self.saveandrestorebreakpoints()

    def isrpdbbreakpoint(self, filepath, lineno):
        if filepath.find("rpdb2.py") == -1:
            return False
        bpinfile = self.breakpoints.get(filepath)
        if not bpinfile:
            return True
        if not bpinfile.get(lineno):
            return True
        return False

    def attach(self, outputfn, abortfn):
        if self.pid:
            tries = 0
            ex = None
            while tries != 5:
                sleep(1)
                util.Log("[PyDbg][info] Trying to Attach")
                ex = None
                try:
                    self.sessionmanager.attach(self.pid, encoding = rpdb2.detect_locale())
                    self.attached = True
                    self.debuggeroutput = outputfn
                    self.abort = abortfn
                    break
                except Exception, ex:
                    tries = tries + 1
            self.pid = None
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (self.mainwindow.GetId(), False))
            if ex:
                err = rpdb2.g_error_mapping.get(type(ex), repr(ex))
                err = "Failed to attach. Error: %s" % err
                util.Log("[PyDbg][err] %s" % err)
                outputfn("\n%s" % err)
                PyToolsUtils.error_dialog(self.mainwindow, err)
                abortfn()
                return
            util.Log("[PyDbg][info] Running")
            outputfn("\nDebugger attached. Program output starts now...\n")

    def attached_callsessionmanagerfn(self, fn, tdexc_clrvars, *args, **kwargs):
        if not self.attached:
            return None
        ex = None
        try:
            return fn(*args, **kwargs)
        except rpdb2.NotAttached, ex:
            self.attached = False
        except (rpdb2.ThreadDone, rpdb2.NoThreads), ex:
            if tdexc_clrvars:
                self.clearlocalvariables()
                self.clearglobalvariables()
                self.clearexceptions()
                return
            util.Log("[PyDbg][err] %s" % traceback.format_exc())
        except Exception, ex:
            util.Log("[PyDbg][err] %s" % traceback.format_exc())
        if self.mainwindow:
            err = rpdb2.g_error_mapping.get(type(ex), repr(ex))
            PyToolsUtils.error_dialog(self.mainwindow, err)
        return None
    
    def callsessionmanagerfn(self, fn, *args, **kwargs):
        ex = None
        try:
            return fn(*args, **kwargs)
        except Exception, ex:
            util.Log("[PyDbg][err] %s" % traceback.format_exc())
        if self.mainwindow:
            err = rpdb2.g_error_mapping.get(type(ex), repr(ex))
            PyToolsUtils.error_dialog(self.mainwindow, err)
        return None
    
    def do_detach(self):
        self.attached_callsessionmanagerfn(self.sessionmanager.detach, False)

    def register_callback(self, func, event_type_dict, fSingleUse = False):
        self.sessionmanager.register_callback(func, event_type_dict, fSingleUse = fSingleUse)

    def install_breakpoints(self):
        self.breakpointmanager.installbreakpoints()
            
    def set_frameindex(self, index):
        self.attached_callsessionmanagerfn(self.sessionmanager.set_frame_index, False, index)
            
    def get_frameindex(self):
        return self.attached_callsessionmanagerfn(self.sessionmanager.get_frame_index, False)
    
    def update_stack(self):
        stacklist = self.attached_callsessionmanagerfn(self.sessionmanager.get_stack, False, [], True)
        if stacklist is not None:
            self.stackframemanager.do_update_stack(stacklist[0])

    def get_thread_list(self):
        res = self.attached_callsessionmanagerfn(self.sessionmanager.get_thread_list, False)
        if res is not None:
            return res
        return (None, {})
    
    def set_thread(self, tid):
        self.attached_callsessionmanagerfn(self.sessionmanager.set_thread, False, tid)
            
    def execute(self, suite):
        return self.attached_callsessionmanagerfn(self.sessionmanager.execute, False, suite)

    def evaluate(self, suite):
        return self.attached_callsessionmanagerfn(self.sessionmanager.evaluate, False, suite)

    def update_namespace(self):
        self.variablesmanager.update_namespace()

    def get_namespace(self, expressionlist, filterlevel):
        return self.attached_callsessionmanagerfn(self.sessionmanager.get_namespace, True, expressionlist, filterlevel)

    def set_synchronicity(self, synchronicity):
        self.callsessionmanagerfn(self.sessionmanager.set_synchronicity, synchronicity)
        
    def get_synchronicity(self):
        return self.callsessionmanagerfn(self.sessionmanager.get_synchronicity)
        
    def set_trap_unhandled_exceptions(self, trap):
        self.callsessionmanagerfn(self.sessionmanager.set_trap_unhandled_exceptions, trap)
        
    def get_trap_unhandled_exceptions(self):
        return self.callsessionmanagerfn(self.sessionmanager.get_trap_unhandled_exceptions)
        
    def set_fork_mode(self, forkmode, autofork):
        self.callsessionmanagerfn(self.sessionmanager.set_fork_mode, forkmode, autofork)
        
    def get_fork_mode(self):
        return self.callsessionmanagerfn(self.sessionmanager.get_fork_mode)
        
    def set_encoding(self, encoding, escaping):
        self.callsessionmanagerfn(self.sessionmanager.set_fork_mode, encoding, escaping)
        
    def get_encoding(self):
        return self.callsessionmanagerfn(self.sessionmanager.get_encoding)
        
    def set_analyze(self, analyze):
        self.attached_callsessionmanagerfn(self.sessionmanager.set_analyze, False, analyze)

    def do_shutdown(self):
        self.attached_callsessionmanagerfn(self.sessionmanager.shutdown, False)
        self.clearstepmarker()
    
    def do_stop(self):
        self.attached_callsessionmanagerfn(self.sessionmanager.stop_debuggee, False)
        self.clearstepmarker()

    def do_restart(self):
        self.attached_callsessionmanagerfn(self.sessionmanager.restart, False)
        self.clearstepmarker()

    def do_jump(self, lineno):
        self.attached_callsessionmanagerfn(self.sessionmanager.request_jump, False, lineno)
        self.clearstepmarker()

    def do_go(self):
        self.attached_callsessionmanagerfn(self.sessionmanager.request_go, False)
        self.clearstepmarker()

    def do_break(self):
        self.attached_callsessionmanagerfn(self.sessionmanager.request_break, False)

    def do_step(self): # Step In
        self.attached_callsessionmanagerfn(self.sessionmanager.request_step, False)
        self.clearstepmarker()

    def do_next(self): # Step Over
        self.attached_callsessionmanagerfn(self.sessionmanager.request_next, False)
        self.clearstepmarker()

    def do_return(self):
        self.attached_callsessionmanagerfn(self.sessionmanager.request_return, False)
        self.clearstepmarker()

    def run_toline(self, filename, lineno):
        self.attached_callsessionmanagerfn(self.sessionmanager.request_go_breakpoint, False, filename, '', lineno)
        self.clearstepmarker()

    def disable_breakpoint(self, bpid):
        self.attached_callsessionmanagerfn(self.sessionmanager.disable_breakpoint, False, [bpid], False)

    def enable_breakpoint(self, bpid):
        self.attached_callsessionmanagerfn(self.sessionmanager.enable_breakpoint, False, [bpid], False)

    def load_breakpoints(self):
        try:
            self.sessionmanager.load_breakpoints()
        except rpdb2.NotAttached:
            pass
        except IOError:
            pass
    
    def clear_breakpoints(self):
        self.attached_callsessionmanagerfn(self.sessionmanager.delete_breakpoint, False, [], True)
        
    def set_breakpoint(self, filepath, lineno, exprstr = "", enabled=True):
        return self.attached_callsessionmanagerfn(self.sessionmanager.set_breakpoint, False, filepath, '', lineno, enabled, exprstr)

    def get_breakpoints(self):
        return self.attached_callsessionmanagerfn(self.sessionmanager.get_breakpoints, False)

    def delete_breakpoint(self, filepath, lineno):
        bps = self.get_breakpoints()
        if not bps:
            return
        for bp in bps.values():            
            if bp.m_lineno == lineno and bp.m_filename == filepath:
                self.attached_callsessionmanagerfn(self.sessionmanager.delete_breakpoint, False, [bp.m_id], False)
