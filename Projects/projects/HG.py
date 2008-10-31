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
from SourceControl import SourceControl, DecodeString

#-----------------------------------------------------------------------------#

class HG(SourceControl):
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
    
    def getRepository(self, path):
        """ Get the repository of a given path """
        # Make sure path is under source control
        if not self.isControlled(path):
            return

        # Get the directory of the given path
        if not os.path.isdir(path):
            path = os.path.dirname(path)

        rline = u''
        # TODO recurse back till .hg directory is found
        #

        return rline
    
    def isControlled(self, path):
        """ Is the path controlled by HG?
        @param path: string

        """
        # If a directory just check if it has a .hg directory
        if os.path.isdir(path):
            if os.path.isfile(os.path.join(path, '.hg', 'store')):
                return True

        # See if the path is in the store directory
        base = self.findHg(path)
        if base is None:
            return False

        store = os.path.join(base, '.hg', 'store', 'data')
        relpath = path.replace(base, u'', 1)
        datapath = os.path.join(store, relpath)
        if os.path.isfile(path):
            datapath += '.i'

        if os.path.exists(datapath):
            return True

        return False
        
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

    def findHg(self, path):
        """Walk the path until the .hg directory is found
        @return: hg path or None

        """
        if not os.path.exists(path):
            return None

        if not os.path.isdir(path):
            path = os.path.dirname(path)

        tmp = path.split(os.path.sep)
        # TODO test this on windows
        if not sys.platform.startswith("win"):
            tmp.insert(0, '/')

        plen = len(tmp)
        pjoin = os.path.join
        for piece in xrange(plen):
            root = pjoin(*tmp[:plen - piece])
            if os.path.exists(pjoin(root, '.hg', 'store')):
                return root + os.path.sep

        return None

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

#        """
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
        codes = {' ':'uptodate', 'A':'added', 'C':'conflict', 'R':'deleted',
                 'M':'modified'}

        # NOTE: HG status command lists all files status relative to the
        #       root of the repository!!
        options = ['status', '-v']
        if not recursive:
            options.append('-N')

        root, files = self.splitFiles(paths)
        out = self.run(root, options + self.getAuthOptions(root) + files)
        if out:
            for line in out.stdout:
                self.log(line)
                code = line[0]
                if code in '!?':
                    continue

                tmp = line[8:].strip().split(' ', 1)
                # 
                if len(tmp) != 2:
                    continue

                workrev, line = tmp
                rev, line = line.strip().split(' ', 1)
                author, line = line.strip().split(' ', 1)
                name = line.strip()
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
        
    def salt(self):
        return '"\x17\x9f/D\xcf'
    salt = property(salt)

#-----------------------------------------------------------------------------#
if __name__ == '__main__':
    hg = HG()
    hg.add([''])
