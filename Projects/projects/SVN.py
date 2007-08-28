#!/usr/bin/env python

import re, os
from SourceControl import SourceControl

class SVN(SourceControl):

    command = 'svn'
    
    def isControlled(self, path):
        """ Is the path controlled by CVS? """
        if os.path.isdir(path):
            if os.path.isfile(os.path.join(path,'.svn','entries')):
                return True
        path, basename = os.path.split(path)
        svndir = os.path.join(path,'.svn')
        if os.path.isdir(svndir):
            try:
                entries = open(os.path.join(svndir,'entries')).read()
                entries = [x.strip().split('\n')[0] for x in entries.split('\x0c') 
                                                    if x.strip()][1:]
                return basename in entries
            except (IOError, OSError):
                pass
        return False
        
    def add(self, paths):
        """ Add paths to the repository """
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['add'] + files)
            self.logOutput(out)
        
    def checkout(self, paths):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['checkout'] + files)
            self.logOutput(out)
        
    def commit(self, paths, message=''):
        """ Commit paths to the repository """
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['commit', '-m', message] + files)
            self.logOutput(out)
                                   
    def diff(self, paths):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['diff'] + files)
            self.closeProcess(out)
        
    def history(self, paths, history=None):
        if history is None:
            history = []
        for path in paths:
            root, files = self.splitFiles(path)
            for file in files:
                out = self.run(root, ['log', file])
                if out:
                    for line in out.stdout:
                        self.log(line)
                        if line.strip().startswith('-----------'):
                            current = {'path':file}
                            history.append(current)
                            for data in out.stdout:
                                self.log(data)
                                rev, author, date, lines = data.split(' | ')
                                current['revision'] = rev
                                current['author'] = author
                                current['date'] = date
                                current['log'] = ''
                                self.log(out.stdout.next())
                                break
                        else:
                            current['log'] += line
                self.logOutput(out)
                history.pop()
        return history
        
    def remove(self, paths):
        """ Recursively remove paths from repository """
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['remove','--force'] + files)
            self.logOutput(out)
        
    def status(self, paths, recursive=False, status={}):
        """ Get SVN status information from given file/directory """
        codes = {' ':'uptodate', 'A':'added', 'C':'conflict', 'D':'deleted',
                 'M':'modified'}
        options = ['status', '-v']
        if not recursive:
            options.append('-N')
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, options + files)
            if out:
                for line in out.stdout:
                    self.log(line)
                    code = line[0]
                    if code == '?':
                        continue
                    workrev, line = line[8:].strip().split(' ', 1)
                    rev, line = line.strip().split(' ', 1)
                    author, line = line.strip().split(' ', 1)
                    name = line.strip()
                    current = status[name] = {}
                    try: current['status'] = codes[code]
                    except KeyError: pass
                self.logOutput(out)
        return status

    def update(self, paths):
        """ Recursively update paths """
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['update'] + files)
            self.logOutput(out)
            
    def revert(self, paths):
        """ Recursively revert paths to repository version """
        for path in paths:
            root, files = self.splitFiles(path)
            if not files:
                files = ['.']
            out = self.run(root, ['revert','-R'] + files)
            self.logOutput(out)
            
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
            
            out = self.run(root, ['cat'] + options+ files)
            if out:
                output.append(out.stdout.read())
                self.logOutput(out)
            else:
                output.append(None)
        return output
               
if __name__ == '__main__':
    svn = SVN()
    svn.add(['/Users/kesmit/pp/editra-plugins/Projects/projects/Icons'])