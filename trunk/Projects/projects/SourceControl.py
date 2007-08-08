#!/usr/bin/env python

import os, fnmatch, subprocess

class SourceControl(object):

    TYPE_FILE = 1
    TYPE_DIRECTORY = 2
    TYPE_ANY = 3   

    filters = []
    command = ''

    def getWorkingDirectory(self, path):
        if os.path.isdir(path):
            return path
        return os.path.dirname(path)

    def addRootOption(self, directory, options):
        """ Add the repository root option to the command """
        return options

    def isControlled(self, directory):
        """ Is the directory controlled by source control? """
        return False

    def run(self, directory, options, env=None):
        """ Run a CVS command in the given directory with given options """
        print directory, self.command, ' '.join(options)
        #return
        try:
            return subprocess.Popen([self.command] +
                                    self.addRootOption(directory, options),
                                    cwd=directory,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    close_fds=True,
                                    env=env).stdout
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

