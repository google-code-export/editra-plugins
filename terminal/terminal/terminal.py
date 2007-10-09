# -*- coding: utf-8 -*-
###############################################################################
# Name: terminal.py                                                           #
# Purpose: Cody Precord                                                       #
# Author: Cody Precord <cprecord@editra.org                                   #
# Copyright: (c) 2007 Cody Precord <staff@editra.org>                         #
# Licence: wxWindows Licence                                                  #
###############################################################################

#-----------------------------------------------------------------------------#
# Imports

import sys
import os
import string
import signal
import re
import time
import wx
import wx.stc

# On windows need to use pipes as pty's are not available
try:
    if sys.platform == 'win32':
        import popen2
        import stat
        USE_PTY   = False
    else:
        import pty
        import tty
        import select
        USE_PTY   = True
except ImportError, msg:
    print "Error importing required libs: %s" % str(msg)

#-----------------------------------------------------------------------------#
# Globals

SHELL = os.environ['SHELL']
if SHELL == '':
    if sys.platform == 'win32':
        SHELL = 'cmd.exe'
    else:
        SHELL = '/bin/sh'

DEBUG = True

#-----------------------------------------------------------------------------#
class Xterm(wx.stc.StyledTextCtrl):
    """Creates a graphical console that works like the system shell
    that it is running on (bash, command, ect...).

    """
    def __init__(self, parent, ID):
        wx.stc.StyledTextCtrl.__init__(self, parent, ID)

        # Attributes
        self._fpos = 0          # First allowed cursor position
        self._exited = False    # Is shell still running
        # Setup
        self.__Configure()
        self.__ConfigureStyles()
        self.__ConfigureKeyCmds()
        self._SetupPTY()
        self.NewPrompt()

        # Event Handlers
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

    def __ConfigureKeyCmds(self):
        """Clear the builtin keybindings that we dont want"""
        self.CmdKeyClear(ord('U'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('Z'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(wx.WXK_BACK, wx.stc.STC_SCMOD_CTRL | wx.stc.STC_SCMOD_SHIFT)
        self.CmdKeyClear(wx.WXK_DELETE, wx.stc.STC_SCMOD_CTRL | wx.stc.STC_SCMOD_SHIFT)
        self.CmdKeyClear(ord('['), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord(']'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('\\'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('/'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('L'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('D'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('Y'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('T'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(wx.WXK_TAB, wx.stc.STC_SCMOD_NORM)

    def __Configure(self):
        """Configure the base settings of the control"""
        self.SetLexer(wx.stc.STC_LEX_NULL)
        self.SetEOLMode(wx.stc.STC_EOL_LF)
        self.SetViewWhiteSpace(False)
        self.SetTabWidth(0)
        self.SetUseTabs(False)
        self.SetWrapMode(True)
        self.SetEndAtLastLine(False)

    def __ConfigureStyles(self):
        """Configure the text coloring of the terminal"""
        # Clear Styles
        self.StyleResetDefault()
        self.StyleClearAll()

        # Set margins
        self.SetMargins(4, 4)
        self.SetMarginWidth(wx.stc.STC_MARGIN_NUMBER, 0)

        # Caret styles
        self.SetCaretWidth(4)
        self.SetCaretForeground(wx.NamedColor("white"))

        # Configure text styles
        font = wx.Font(11, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, 
                       wx.FONTWEIGHT_NORMAL)
        face = font.GetFaceName()
        size = font.GetPointSize()
        fore = "#FEFEFE"
        back = "#000000"
        self.StyleSetSpec(0, "face:%s,size:%d,fore:%s,back:%s,bold" % (face, size, fore, back))
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, \
                          "face:%s,size:%d,fore:%s,back:%s,bold" % (face, size, fore, back))
        self.StyleSetSpec(wx.stc.STC_STYLE_CONTROLCHAR, \
                          "face:%s,size:%d,fore:%s,back:%s" % (face, size, fore, back))

        self.Colourise(0, -1)

    def __del__(self):
        DebugLog("[terminal][info] Terminal instance is being deleted")
        self._CleanUp()

    #---- Protected Members ----#
    def _CheckAfterExe(self):
        """Check std out for anything left after an execution"""
        DebugLog("[terminal][info] Checking after cmd execution")
        self.Read()
        self.CheckForPassword()

    def _CleanUp(self):
        """Cleanup open file descriptors"""
        if self._exited:
            DebugLog("[terminal][exit] Already exited")
            return

        try:
            DebugLog("[terminal][exit] Closing FD and killing process")
            if not USE_PTY:
                os.close(self.ind)
                os.close(self.outd)

            os.close(self.errd)       ##  all the same if pty
            if USE_PTY:
                os.kill(self.pid, signal.SIGKILL)
                time.sleep(self.delay) # give some time for the process to die

        except Exception, msg:
            DebugLog("[terminal][err] %s" % str(msg))

        DebugLog("[terminal][cleanup] Finished Cleanup")

    def _EndRead(self, any_lines_read):
        """Finish up after reading"""
        # Mark earliest valid cursor position in buffer
        self._fpos = self.GetCurrentPos()
        if (not USE_PTY and any_lines_read):
            self.LineDelete()
            DebugLog("[terminal][endread] Deleted trailing line")
            self._fpos = self.GetCurrentPos()

        DebugLog("[terminal][info] Set valid cursor to > %d" % self._fpos)
#         self.ScrollToLine(self.GetCurrentLine())
        self.EnsureCaretVisible()

    def _HandleExit(self, cmd):
        """Handle closing the shell connection"""
        ##  Exit was typed, could be the spawned shell, or a subprocess like
        ##  telnet/ssh/etc.
        DebugLog("[terminal][exit] Exiting process")
        if not self._exited:
            try:
                DebugLog("[terminal][exit] Shell still around so trying to close")
                self.Write(cmd + '\n')
                self._CheckAfterExe()
            except Exception, msg:            
                DebugLog("[terminal][err] Exception on exit: %s" % str(msg))

                ## shell exited, self._exited may not have been set yet in
                ## sigchld_handler.
                DebugLog("[terminal][exit] Shell Exited is: " + str(self._exited))
                self.ExitShell()

    def _ProcessRead(self, lines):
        """Process the raw lines from stdout"""
        DebugLog("[terminal][info] Processing Read...")
        lines_to_print = lines.split('\n')

        #  Filter out invalid blank lines from begining/end input
        if sys.platform == 'win32':
            m = re.search(re.escape(self.last_cmd_executed.strip()), lines_to_print[0])
            if m != None or lines_to_print[0] == "":
                DebugLog('[terminal][info] Win32, removing leading blank line')
                lines_to_print = lines_to_print[ 1: ]

        num_lines = len(lines_to_print)
        if num_lines > 1:
            last_line = lines_to_print[num_lines - 1].strip()

            if last_line == "":
                lines_to_print = lines_to_print[ :-1 ]

        errors = self.CheckStdErr()
        if errors:
            DebugLog("[terminal][err] Process Read Prepending stderr --> ")
            lines_to_print = errors + lines_to_print

        return lines_to_print

    def _SetupPTY(self):
        """Setup the connection to the real terminal"""
        if USE_PTY:
            ##  The lower this number is the more responsive some commands
            ##  may be ( printing prompt, ls ), but also the quicker others
            ##  may timeout reading their output ( ping, ftp )
            self.delay = 0.1

            self.master, pty_name = pty.master_open()
            DebugLog("[terminal][info] Slave Pty name: " + pty_name)

            self.pid, self.fd = pty.fork()

            self.outd = self.fd
            self.ind  = self.fd
            self.errd = self.fd

            signal.signal(signal.SIGCHLD, self._SigChildHandler)

            if self.pid == 0:
                ##  In spawned shell process, NOTE: any 'print'ing done within
                ##  here will corrupt vim.
                attrs = tty.tcgetattr( 1 )

                attrs[ 6 ][ tty.VMIN ]  = 1
                attrs[ 6 ][ tty.VTIME ] = 0
                attrs[ 0 ] = attrs[ 0 ] | tty.BRKINT
                attrs[ 0 ] = attrs[ 0 ] & tty.IGNBRK
                attrs[ 3 ] = attrs[ 3 ] & ~tty.ICANON & ~tty.ECHO

                tty.tcsetattr(1, tty.TCSANOW, attrs)
                os.execv(SHELL, [ SHELL, ])

            else:
                try:
                    attrs = tty.tcgetattr(1)
                    termios_keys = attrs[6]
                except:
                    DebugLog('[terminal][err] tcgetattr failed')
                    return

                #  Get *real* key-sequence for standard input keys, i.e. EOF
                self.eof_key   = termios_keys[ tty.VEOF ]
                self.eol_key   = termios_keys[ tty.VEOL ]
                self.erase_key = termios_keys[ tty.VERASE ]
                self.intr_key  = termios_keys[ tty.VINTR ]
                self.kill_key  = termios_keys[ tty.VKILL ]
                self.susp_key  = termios_keys[ tty.VSUSP ]
        else:
            ##  Use pipes on Win32. not as reliable/nice. works OK but with limitations.
            self.delay = 0.2

            try:
                import win32pipe
                DebugLog('[terminal][info] using windows extensions')
                self.stdin, self.stdout, self.stderr = win32pipe.popen3( self.sh + " " + self.arg )
            except ImportError:
                DebugLog('[terminal][info] not using windows extensions')
                self.stdout, self.stdin, self.stderr = popen2.popen3( self.sh + " " + self.arg, -1, 'b' )

            self.outd = self.stdout.fileno()
            self.ind  = self.stdin.fileno()
            self.errd = self.stderr.fileno()

            self.intr_key = ''
            self.eof_key  = ''

    def _SigChildHandler(self, sig, frame):
        """Child process signal handler"""
        DebugLog("[terminal][info] caught SIGCHLD")
        self._WaitPid()

    def _WaitPid(self):
        """Mark the original shell process as having gone away if it
        has exited.

        """
        if os.waitpid(self.pid, os.WNOHANG)[0]:
            self._exited = True
            DebugLog("[terminal][waitpid] Shell process has exited")
        else:
            DebugLog("[terminal][waitpid] Shell process hasn't exited")

    #---- End Protected Members ----#

    #---- Public Members ----#
    def CheckForPassword(self):
        """Check if the shell is waiting for a password or not"""
        prev_line = self.GetLine(self.GetCurrentLine() - 1)
        for regex in ['^\s*Password:',         ##  su, ssh, ftp
                      'password:',             ##  ???, seen this somewhere
                      'Password required' ]:    ##  other ftp clients:
            if re.search(regex, prev_line):
                try:
                    print "FIX ME"
#                     vim.command( 'let password = inputsecret( "Password? " )' )
                except KeyboardInterrupt:
                    return

#                 password = vim.eval( "password" )
#                 self.execute_cmd( [password] )       ##  recursive call here...

    def CheckStdErr(self):
        """Check for errors in the shell"""
        errors  = ''
        if sys.platform == 'win32':
            err_txt  = self.PipeRead(self.errd, 0)
            errors   = err_txt.split('\n')

            num_lines = len(errors)
            last_line = errors[num_lines - 1].strip()

            if last_line == "":
                errors = errors[ :-1 ]

        return errors

    def ClearScreen(self):
        """Clear the screen so that all commands are scrolled out of
        view and a new prompt is shown on the top of the screen.

        """
        self.Write("\n")
        self._CheckAfterExe()
        self.ScrollLines(self.LinesOnScreen())

    def ExecuteCmd(self, cmd=None, null=1):
        """Run the command entered in the buffer"""
        DebugLog("terminal][exec] Running command: %s" % str(cmd))

        try:
            # Get text from prompt to eol when no command is given
            if cmd is None:
                cmd = self.GetTextRange(self._fpos, self.GetLength())

            cmd = cmd.strip()
            if re.search( r'^\s*\bclear\b', cmd) or re.search( r'^\s*\bcls\b', cmd):
                DebugLog('[terminal][exec] Clear Screen')
                self.ClearScreen()

            elif re.search( r'^\s*\exit\b', cmd):
                DebugLog('[terminal][exec] Exit terminal session')
                self._HandleExit(cmd)

            else:
                if null:
                    self.Write(cmd + '\n')
                else:
                    self.Write(cmd)

                self._CheckAfterExe()

            self.last_cmd_executed = cmd

        except KeyboardInterrupt:
            pass

    def ExitShell(self):
        """Cause the shell to exit"""
        if not self._exited:
            self._CleanUp()

        self.PrintLines(["[process complete]\n"])
        self.SetReadOnly(True)

    def NewPrompt(self):
        """Put a new prompt on the screen and make all text from end of
        prompt to left read only.

        """
        self.ExecuteCmd("")

    def OnKeyDown(self, evt):
        """Handle key down events"""
        if self._exited:
            return

        key = evt.GetKeyCode()
        if key == wx.WXK_RETURN:
            self.CmdKeyExecute(wx.stc.STC_CMD_NEWLINE)
            self.ExecuteCmd()
        elif key == wx.WXK_TAB:
            # TODO Tab Completion
            pass
        elif key == wx.WXK_HOME:
            # Go Prompt Start
            self.GotoPos(self._fpos)
        else:
            evt.Skip()

    def OnChar(self, evt):
        """Handle character enter events"""
        evt.Skip()

    def OnKeyUp(self, evt):
        """Handle when the key comes up"""
        evt.Skip()

    def PrintLines(self, lines):
        """Print lines to the terminal buffer
        @param lines: list of strings

        """
        num_lines = len(lines)
        for line in lines:
            DebugLog("[terminal][print] Current line is --> %s" % line)
            m = None
            while re.search( '\r$', line):
                DebugLog('[terminal][print] removing trailing ^M' )
                line = line[ :-1 ]
                m = True

            # Put the line
            self.AppendText(line)

            # Move cursor to end of buffer
            self._fpos = self.GetLength()
            self.GotoPos(self._fpos)

            ##  If there's a '\n' or using pipes and it's not the last line
            if not USE_PTY or m:
                DebugLog("[terminal][print] Appending new line since ^M or not using pty")
                self.AppendText("\n")

    def PipeRead(self, pipe, minimum_to_read):
        """Read from pipe used on Windows due to lack of support for select
        to be used with anything outside of sockets.

        """
        DebugLog("[terminal][pipe] minimum to read is " + str(minimum_to_read))
        DebugLog("[terminal][pipe] sleeping for %s seconds" % str(self.delay))

        time.sleep(self.delay)

        count = 0
        count = os.fstat(pipe)[stat.ST_SIZE]
        data = ''
        DebugLog("[terminal][pipe]: initial count via fstat is " + str(count))

        while (count > 0):
            tmp = os.read(pipe, 1)
            data += tmp

            count = os.fstat(pipe)[stat.ST_SIZE]
            if len(tmp) == 0:
                DebugLog("[terminal][pipe] count %s but nothing read" % str(count))
                break

            #  Be sure to break the read, if asked to do so,
            #  after we've read in a line termination.
            if minimum_to_read != 0 and len(data) > 0 and data[len(data) - 1] == '\n':
                if len(data) >= minimum_to_read:
                    DebugLog("[terminal][pipe] read minimum and found termination")
                    break
                else:
                    dbg_print("[terminal][pipe] more data to read: count is " + str(count))

        return data

    def Read(self):
        """Read output from stdin"""
        num_iterations       = 0      ##  counter for periodic redraw
        any_lines_read       = 0      ##  sentinel for reading anything at all

        while 1:
            if USE_PTY:
                r, w, e = select.select([self.outd], [], [], self.delay)
            else:
                r = [1,]  # pipes, unused, fake it out so I don't have to special case

            for file_iter in r:
                lines = ''
                if USE_PTY:
                    lines = os.read(self.outd, 32)
                else:
                    lines = self.PipeRead(self.outd, 2048)

                if lines == '':
                    DebugLog('[terminal][read] No more data on stdout pipe_read')
                    r = []
                    break

                any_lines_read  = 1 
                num_iterations += 1

                lines = self._ProcessRead(lines)
                self.PrintLines(lines)

            if not len(r):
                DebugLog('[terminal][info] End of Read' )
                self._EndRead(any_lines_read)
                break

    def Write(self, cmd):
        """Write out command to shell process"""
        DebugLog("[terminal][info] Writting out command: " + cmd)
        os.write(self.ind, cmd)

#-----------------------------------------------------------------------------#
# Utility Functions
def DebugLog(msg):
    """Print debug messages"""
    if DEBUG:
        print msg

#-----------------------------------------------------------------------------#
# For Testing

if __name__ == '__main__':
    app = wx.PySimpleApp(False)
    frame = wx.Frame(None, wx.ID_ANY, "Terminal Test")
    term = Xterm(frame, wx.ID_ANY)
    
    fsizer = wx.BoxSizer(wx.VERTICAL)
    fsizer.Add(term, 1, wx.EXPAND)
    frame.SetSizer(fsizer)
    
    frame.SetSize((600, 400))
    frame.Show()
    app.MainLoop()
