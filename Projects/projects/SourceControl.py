#!/usr/bin/env python

import os, fnmatch, subprocess, sys

class SourceControl(object):

    TYPE_FILE = 1
    TYPE_DIRECTORY = 2
    TYPE_ANY = 3   

    filters = []
    command = ''
    
    def __init__(self, console=None):
        if console is None:
            self.console = sys.stdout
        else:
            self.console = console

    def splitFiles(self, path, forcefiles=False, type=None, topdown=True):
        """ 
        Split path into a working directory and list of files 
        
        Required Arguments:
        path -- path to split
        forcefiles -- boolean indicating if the list of recursive files
            should be returned explicitly
        type -- type of files/directories to return
        topdown -- boolean indicating if the files should be listed
            before directories
            
        Returns: two element tuple where the first element is the 
            starting directory and the second element is a list of the
            files in that directory tree.  The file list will be
            empty if forcefiles is False and the path passed in is a 
            directory.
        
        """
        root, files = path, []
        if not os.path.isdir(path):
            root, files = os.path.split(path)
            files = self.filterPaths([files])
        elif forcefiles:
            files = self.getPathList(path, type, topdown)
        return root, files

    def addRootOption(self, directory, options):
        """ Add the repository root option to the command """
        return options

    def isControlled(self, directory):
        """ Is the directory controlled by source control? """
        return False

    def run(self, directory, options, env={}, mergeerr=False):
        """ Run a CVS command in the given directory with given options """
        self.console.write('%s %s %s\n' % (directory, self.command, ' '.join(options)))
        #return
        environ = os.environ.copy()
        environ.update(env)
        environ['CVS_RSH'] = 'ssh'
        try:
            stderr = subprocess.PIPE
            if mergeerr:
                stderr = subprocess.STDOUT
            return subprocess.Popen([self.command] +
                                    self.addRootOption(directory, options),
                                    cwd=directory,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=stderr,
                                    env=environ)
        except OSError: 
            pass
        
    def filterPaths(self, paths):
        """" Filter out paths based on class filters """
        newpaths = []
        for path in paths:
            if path.endswith('\r'):
                continue
            for pattern in self.filters:
                if fnmatch.fnmatchcase(path, pattern):
                    continue
            newpaths.append(path)
        return newpaths

    def getPathList(self, paths, type=None, topdown=True):
        """ 
        Return the full list of files and directories 
        
        If the list of paths contains a file, that file is added to
        the output list.  If the path is a directory, that directory
        and everything in that directory is added recursively.

        Required Arguments:
        paths -- list of file paths
        type -- constant indicating which type of objects to return
            Can be one of: TYPE_FILE, TYPE_DIRECTORY, TYPE_ANY
        topdown -- topdown argument passed to os.walk
        
        """
        newpaths = []
        if type is None:
            type = self.TYPE_ANY
        for path in paths:
            if os.path.isdir(path):
                if not path.endswith(os.path.sep):
                    path += os.path.sep
                # Add current directory if parent directory is CVS controlled
                if self.isControlled(os.path.join(path,'..')):
                    if type != self.TYPE_FILE:
                        newpaths.append(os.path.basename(path))
                # Add all files/directories recursively
                for root, dirs, files in os.walk(path, topdown):
                    root = root[len(path):]
                    if type != self.TYPE_FILE:
                        for dir in dirs:
                            newpaths.append(os.path.join(root,dir))
                    if type != self.TYPE_DIRECTORY:
                        for file in files:
                            newpaths.append(os.path.join(root,file))
            elif type != self.TYPE_DIRECTORY:
                newpaths.append(os.path.basename(path))
        return self.filterPaths(newpaths)

    def log(self, s):
        if hasattr(self.console, 'write'):
            self.console.write(s)
        elif hasattr(self.console, 'WriteText'):
            self.console.WriteText(s)

    def logOutput(self, p, close=True):
        """ Read and print stdout/stderr """
        if not p:
            return
        flush = write = None
        if hasattr(self.console, 'write'):
            write = self.console.write
        elif hasattr(self.console, 'WriteText'):
            write = self.console.WriteText
        if hasattr(self.console, 'flush'):
            flush = self.console.flush
        while write:
            err = out = None
            if p.stderr:
                err = p.stderr.readline()
                if err:
                    write(err)
                    if flush:
                        flush()
            if p.stdout:
                out = p.stdout.readline()
                if out:
                    write(out)
                    if flush:
                        flush()
                if not err and not out:
                    return
        if close:
            self.closeProcess(p)

    def closeProcess(self, p):
        try: p.stdout.close()
        except: pass
        try: p.stderr.close()
        except: pass
        try: p.stdin.close()
        except: pass