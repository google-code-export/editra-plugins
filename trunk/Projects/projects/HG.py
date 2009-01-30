###############################################################################
# Name: HG.py                                                                 #
# Purpose: Mercurial Source Control Implementation                            #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################
"""Mercurial implementation of the SourceControl object
@note: Just a stub, not usable nor functional (yet)

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__revision__ = "$Revision$"
__scid__ = "$Id$"

#-----------------------------------------------------------------------------#

import os
import re
import datetime

# Local imports
import crypto
import SourceControl

#-----------------------------------------------------------------------------#

class HG(SourceControl.SourceControl):
    """ Mercurial source control class """
    name = 'Mercurial'
    command = 'hg'

    def __repr__(self):
        return 'HG.HG()'
        
#    def getAuthOptions(self, path):
#        """ Get the repository authentication info """
#        output = []
#        options = self.getRepositorySettings(path)
#        if options.get('username', ''):
#            output.append('--username')
#            output.append(options['username'])
#        if options.get('password', ''):
#            output.append('--password')
#            output.append(crypto.Decrypt(options['password'], self.salt))
#        return output

    def findRoot(self, path):
        """Find the repository root for given path"""
        root = SourceControl.searchBackwards(path, checkDirectory)

        if root is None:
            return None
        else:
            return root + os.path.sep

    def getRepository(self, path):
        """ Get the repository of a given path """
        # Make sure path is under source control
        root = self.findRoot(path)
        if root is None:
            return None
        else:
            return root
    
    def isControlled(self, path):
        """ Is the path controlled by HG?
        @param path: string

        """
        root = self.findRoot(path)
        if root is None:
            return False

        # Path is in repo path so now check if it is tracked or not
#        for item in self.untrackedFiles(path):
#            if path.startswith(item):
#                return False
#        else:
        return True

    def add(self, paths):
        """ Add paths to the repository 
        @param paths: list of strings

        """
#        root, files = self.splitFiles(paths)
#        if '.' in files:
#            root, parent = os.path.split(root)
#            if not parent:
#                root, parent = os.path.split(root)
#            for i, f in enumerate(files):
#                files[i] = os.path.join(parent, f)

#        out = self.run(root, ['add'] + files)
#        self.logOutput(out)
        
    def checkout(self, paths):
        """ Checkout files at the given path 
        @param paths: list of strings

        """
#        root, files = self.splitFiles(paths)
#        out = self.run(root, ['checkout', '--non-interactive'] + self.getAuthOptions(root) + files)
#        self.logOutput(out)
        
    def commit(self, paths, message=''):
        """ Commit paths to the repository 
        @param paths: list of strings
        @keyword message: commit message string

        """
#        root, files = self.splitFiles(paths)
#        out = self.run(root, ['commit', '-m', message] + files)
#        self.logOutput(out)
                                   
    def diff(self, paths):
        """ Run the diff program on the given files 
        @param paths: list of strings

        """
        root, files = self.splitFiles(paths)
        out = self.run(root, ['diff',] + files)
        self.closeProcess(out)

    def makePatch(self, paths):
        """ Make a patch of the given paths 
        @param paths: list of strings

        """
        root, files = self.splitFiles(paths)
        patches = list()
        for fname in files:
            out = self.run(root, ['diff',] + [fname])
            lines = [ line for line in out.stdout ]
            self.closeProcess(out)
            patches.append((fname, ''.join(lines)))
        return patches

    def history(self, paths, history=None):
        """ Get the revision history of the given paths 
        @param paths: list of strings
        @keyword history: list to return history info in

        """
#        if history is None:
#            history = []

#        root, files = self.splitFiles(paths)
#        for fname in files:
#            out = self.run(root, ['log',] + + [fname])
#            pophistory = False
#            if out:
#                for line in out.stdout:
#                    self.log(line)
#                    if line.strip().startswith('-----------'):
#                        pophistory = True
#                        current = {'path':fname}
#                        history.append(current)
#                        for data in out.stdout:
#                            self.log(data)
#                            rev, author, date, lines = data.split(' | ')
#                            current['revision'] = DecodeString(rev)
#                            current['author'] = DecodeString(author)
#                            current['date'] = self.str2datetime(date)
#                            current['log'] = u''
#                            self.log(out.stdout.next())
#                            break
#                    else:
#                        current['log'] += DecodeString(line)
#            self.logOutput(out)
#            if pophistory:
#                history.pop()
#        return history
    
    def str2datetime(self, s):
        """ Convert a timestamp string to a datetime object """
#        return datetime.datetime(*[int(y) for y in [x for x in re.split(r'[\s+/:-]', s.strip()) if x][:6]])
        
    def remove(self, paths):
        """ Recursively remove paths from repository 
        @param paths: list of strings

        """
        root, files = self.splitFiles(paths)
        out = self.run(root, ['remove', '-f'] + files)
        self.logOutput(out)
        
    def status(self, paths, recursive=False, status=dict()):
        """ Get HG status information from given file/directory 
        @param paths: list of strings
        @keyword recursive: recursivly check status of repository
        @keyword status: dict to return status in

        """
        codes = {' ':'uptodate', 'A':'added', 'C':'uptodate', 'R':'deleted',
                 'M':'modified'}

        # NOTE: HG status command lists all files status relative to the
        #       root of the repository!!
        options = ['status', '-A']

        root, files = self.splitFiles(paths)
        # self.getAuthOptions(root)
        out = self.run(root, options + files)
        if out:
            for line in out.stdout:
                self.log(line)
                code = line[0]

                # Unknown
                if code in '!?':
                    continue

                tmp = line.strip().split(' ', 1)
                if len(tmp) != 2:
                    continue
                name = tmp[1]

                current = status[name] = {}

                try:
                    current['status'] = codes[code]
                except KeyError:
                    pass

            self.logOutput(out)

        return status

    def update(self, paths):
        """ Recursively update paths """
        root, files = self.splitFiles(paths)
        out = self.run(root, ['update',] +  files)
        self.logOutput(out)
            
    def revert(self, paths):
        """ Recursively revert paths to repository version """
#        root, files = self.splitFiles(paths)
#        if not files:
#            files = ['.']

#        out = self.run(root, ['revert', '-R'] + files)
#        self.logOutput(out)
            
    def fetch(self, paths, rev=None, date=None):
        """ Fetch a copy of the paths' contents """
        output = []
        for path in paths:
            if os.path.isdir(path):
                continue
            root, files = self.splitFiles(path)
            
            options = []
            if rev:
                options.append('-r')
                if rev[0] == 'r':
                    rev = rev[1:]
                options.append(rev)

            if date:
                options.append('-r')
                options.append('{%s}' % date)
            
            out = self.run(root, ['cat', '--non-interactive'] + \
                                  options + files)
            if out:
                output.append(out.stdout.read())
                self.logOutput(out)
            else:
                output.append(None)
        return output

    def untrackedFiles(self, path):
        """ Find the untracked files under the given path """
        root = self.splitFiles(path)[0]
        repo = self.findRoot(root)
        out = self.run(root, ['status', '-u'], mergeerr=True)
        unknown = list()
        if out:
            start_unknown = False
            for line in out.stdout:
                if line and line.startswith('?'):
                    line = line.lstrip('?').strip()
                    unknown.append(line)
        return unknown

    def salt(self):
        return '"\x17\x9f/D\xcf'
    salt = property(salt)

#-----------------------------------------------------------------------------#

def checkDirectory(directory):
    """Checks if a given directory is the hg head"""
    if os.path.isdir(directory):
        if os.path.exists(os.path.join(directory, '.hg')):
            return True
    else:
        return False

#-----------------------------------------------------------------------------#
if __name__ == '__main__':
    hg = HG()
    hg.add([''])
