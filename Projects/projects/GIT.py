#!/usr/bin/env python
############################################################################
#    Copyright (C) 2007 Cody Precord                                       #
#    cprecord@editra.org                                                   #
#                                                                          #
#    Editra is free software; you can redistribute it and#or modify        #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    Editra is distributed in the hope that it will be useful,             #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

import os
import sys
import re
from SourceControl import SourceControl

#-----------------------------------------------------------------------------#
NEWPAT = re.compile('#[ \t]+new file:') # added
RNAME = re.compile('#[ \t]+renamed:') # this is odd need more research
COPPAT = rname = re.compile('#[ \t]+copied:') # this is odd need more research
MODPAT = re.compile('#[ \t]+modified:') # modified
DELPAT = re.compile('#[ \t]+deleted:')  # deleted
CONPAT = re.compile('#[ \t]+conflict:') # conflict ??? Couldnt find ref
UNKPAT = re.compile('#[ \t]+[a-zA-Z0-9]+') # hmmm
COMPAT = re.compile('commit [a-z0-9]{40}') # Commit line in log

class GIT(SourceControl):
    """Source control implementation to add GIT support to the 
    Projects Plugin.

    """
    command = 'git'
    
    def isControlled(self, path):
        """ Is the path controlled by GIT? 
        The repository directory is only kept in the root of the
        project so must check recursively from given path to root
        to make sure if it is controlled or not

        """
        def checkDirectory(directory):
            if os.path.isdir(directory):
                if os.path.exists(os.path.join(directory, '.git', 'HEAD')):
                    return True
            else:
                return False

        # First make sure path is under a directory controlled by git
        tmp = path.split(os.path.sep)
        # TODO test this on windows
        if not sys.platform.startswith('win'):
            tmp.insert(0, '/')
        plen = len(tmp)
        for piece in xrange(plen):
            if checkDirectory(os.path.join(*tmp[:plen - piece])):
                break
        else:
            return False

        # Path is in repo path so now check if it is tracked or not
        for item in self.untrackedFiles(path):
            if path.startswith(item):
                return False
        else:
            return True

    def add(self, paths):
        """Add paths to repository"""
        pjoin = os.path.join
        isdir = os.path.isdir
        for path in paths:
            root, files = self.splitFiles(path, forcefiles=True)
            dirs = sorted([x for x in files if isdir(pjoin(root, x))])
            files = sorted([x for x in files if not isdir(pjoin(root, x))])
            # Add all directories individually first
            for d in dirs:
                out = self.run(root, ['add', '-n', d])
                self.logOutput(out)
            # Add all files
            if files:
                out = self.run(root, ['add'] + files)
                self.logOutput(out)                
        
    def checkout(self, paths):
        """Checkout the given paths"""
        root, files = self.splitFiles(paths, forcefiles=True)
        out = self.run(root, ['clone'] + files)
        self.logOutput(out)
            
    def commit(self, paths, message=''):
        """ Commit all files with message """
        root, files = self.splitFiles(paths)
        out = self.run(root, ['commit', '-m', message] + files)
        self.logOutput(out)
            
    def diff(self, paths):
        root, files = self.splitFiles(paths)
        out = self.run(root, ['diff'] + files)
        self.logOutput(out)

    def history(self, paths, history=None):
        """ Get history of the given paths """
        if history is None:
            history = list()
        for path in paths:
            root, files = self.splitFiles(path)
            for file in files:
                out = self.run(root, ['log', file])
                if out:
                    for line in out.stdout:
                        self.log(line)
                        if re.match(COMPAT, line.strip()):
                            current = {'path':file}
                            history.append(current)
                            current['revision'] = line.split()[-1].strip()
                            current['log'] = ''
                        elif line.startswith('Author: '):
                            current['author'] = line.split(' ', 1)[-1]
                        elif line.startswith('Date: '):
                            current['date'] = line.split(' ', 1)[-1].strip()
                        else:
                            current['log'] += line

        # Cleanup log formatting
        for item in history:
            if item.has_key('log'):
                item['log'] = item['log'].strip()

        return history

    def remove(self, paths):
        """ Recursively remove paths from source control """
        # Reverse paths so that files get deleted first
        for path in reversed(sorted(paths)):
            root, files = self.splitFiles(path)           
            out = self.run(root, ['rm', '-R', '-f'] + files)
            self.logOutput(out)

    def findRoot(self, path):
        """Find the repository root for given path"""
        tmp = path.split(os.path.sep)
        # TODO test this on windows
        if not sys.platform.startswith("win"):
            tmp.insert(0, '/')
        plen = len(tmp)
        for piece in xrange(plen):
            root = os.path.join(*tmp[:plen - piece])
            if os.path.exists(os.path.join(root, '.git', 'HEAD')):
                return root + os.path.sep
        return None

    def status(self, paths, recursive=False, status=None):
        """Get the status of all given paths """
        # GIT status shows all status recursivly so need
        #     to parse output and eliminate items that are not part of the
        #     request.
        # NOTE: uptodate files are not listed in output of status

        root = self.splitFiles(paths[0])[0]
        repo = self.findRoot(root)
        out = self.run(root, ['status'], mergeerr=True)
        if out:
            # Collect all file names and status { name : status }
            # NOTE: file names are returned as a relative path to repository
            #       root
            collect = dict()
            unknown = list()
            pjoin = os.path.join
            start_unknown = False
            for line in out.stdout:
                if start_unknown:
                    if re.search(UNKPAT, line):
                        tmp = line.strip().split()
                        unknown.append(os.path.normpath(pjoin(repo, tmp[-1])))
                    continue
                if re.search(NEWPAT, line):
                    tmp = re.sub(NEWPAT, u'', line, 1).strip()
                    if len(tmp):
                        collect[os.path.normpath(pjoin(repo, tmp))] = 'added'
                elif re.search(rname, line):
                    tmp = re.sub(rname, u'', line, 1).strip()
                    if len(tmp):
                        tmp = tmp.split('->')[-1].strip()
                        collect[os.path.normpath(pjoin(repo, tmp))] = 'added'
                elif re.search(COPPAT, line):
                    tmp = re.sub(COPPAT, u'', line, 1).strip()
                    if len(tmp):
                        tmp = tmp.split('->')[-1].strip()
                        collect[os.path.normpath(pjoin(repo, tmp))] = 'added'
                elif re.search(MODPAT, line):
                    tmp = re.sub(MODPAT, u'', line, 1).strip()
                    if len(tmp):
                        collect[os.path.normpath(pjoin(repo, tmp))] = 'modified'
                elif re.search(DELPAT, line):
                    tmp = re.sub(DELPAT, u'', line, 1).strip()
                    if len(tmp):
                        collect[os.path.normpath(pjoin(repo, tmp))] = 'deleted'
                elif re.search(CONPAT, line):
                    tmp = re.sub(CONPAT, u'', line, 1).strip()
                    if len(tmp):
                        collect[os.path.normpath(pjoin(repo, tmp))] = 'conflict'
                elif line.startswith('# Untracked files:'):
                    start_unknown = True
                else:
                    continue
            start_unknown = False

            # Find applicable status information based on given paths
            for path in paths:
                for name, stat in collect.iteritems():
                    name = name.replace(path, u'').strip(os.path.sep)
                    status[name] = {'status' : stat}

                # Mark all update date files
                if not os.path.isdir(path):
                    path = os.path.dirname(path)
                files = os.listdir(path)
                files = [pjoin(path, x) for x in files]
                for fname in files:
                    if fname not in collect and fname not in unknown:
                        # Make sure name is not under an unknown as well
                        for x in unknown:
                            if fname.startswith(x):
                                break
                        else:
                            fname = fname.replace(path, u'').strip(os.path.sep)
                            status[fname] = {'status' : 'uptodate'}
        return status

    def untrackedFiles(self, path):
        """ Find the untracked files under the given path """
        root = self.splitFiles(path)[0]
        repo = self.findRoot(root)
        out = self.run(root, ['status'], mergeerr=True)
        unknown = list()
        if out:
            start_unknown = False
            for line in out.stdout:
                if start_unknown:
                    if re.search(UNKPAT, line):
                        tmp = line.strip().split()
                        tmp = os.path.normpath(os.path.join(repo, tmp[-1]))
                        unknown.append(tmp)
                    continue
                elif line.startswith('# Untracked files:'):
                    start_unknown = True
                else:
                    pass
        return unknown

    def update(self, paths):
        """ Recursively update paths """
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['pull'] + files)
            self.logOutput(out)
            
    def revert(self, paths): 
        """ Revert paths to repository versions """
        for path in paths:
            root, files = self.splitFiles(path, forcefiles=True, 
                                          type=self.TYPE_FILE)
            for file in files:
                out = self.run(root, ['checkout'] + files)
                self.logOutput(out)

    def fetch(self, paths, rev=None, date=None):
        """ Fetch a copy of the paths from the repository """
        output = []
        for path in paths:
            if os.path.isdir(path):
                continue
            root, files = self.splitFiles(path)
            repo = self.findRoot(path)

            # Adjust file names
            files = [ os.path.join(root, f).replace(repo, u'', 1).strip(os.path.sep) for f in files ]
            if rev:
                options = rev + u':%s'
            else:
                options = 'HEAD:%s'
            if date:
                self.logOutput("[git] date not currently supported")

            for f in files:
                out = self.run(root, ['show'] + [options % f])
                if out:
                    content = out.stdout.read() 
                    self.logOutput(out)
                    if content.strip():
                        output.append(content)
                    else:
                        output.append(None)
                else:
                    output.append(None)
        return output
                        
if __name__ == '__main__':
    git = GIT()
    print git.status(['.'], recursive=True)
    print git.history(['setup.py'])
