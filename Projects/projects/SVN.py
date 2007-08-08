#!/usr/bin/env python

import re, os
from SourceControl import SourceControl

class SVN(SourceControl):

    command = 'svn'
    
    def isControlled(self, path):
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        return os.path.isdir(os.path.join(path,'.svn'))

    def add(self, paths):
        for path in paths:
            root = path
            if os.path.isdir(path):
                root = os.path.dirname(path)
            out = self.run(self.getWorkingDirectory(root), 
                           ['add',os.path.basename(path)])
        
    def checkout(self, paths):
        for path in paths:
            root = path
            if os.path.isdir(path):
                root = os.path.dirname(path)
            out = self.run(self.getWorkingDirectory(root), 
                           ['checkout',os.path.basename(path)])
        
    def commit(self, paths, message=''):
        for path in paths:
            root = path
            if os.path.isdir(path):
                root = os.path.dirname(path)
            out = self.run(self.getWorkingDirectory(root), 
                           ['commit','-m',message,os.path.basename(path)])
                                   
    def diff(self, paths):
        for path in paths:
            out = self.run(self.getWorkingDirectory(path), 
                           ['diff'] + self.getPathList([path], type=self.TYPE_FILE))
        
    def history(self, paths):
        history = []
        for path in paths:
            out = self.run(self.getWorkingDirectory(path), 
                           ['log'] + self.getPathList([path]))
            if out:
                revision_re = re.compile(r'^revision\s+(\S+)')
                dasl_re = re.compile(r'^date:\s+(\S+\s+\S+);\s+author:\s+(\S+);\s+state:\s+(\S+);')
                for line in out:
                    if line.startswith('----------'):
                        current = history.append({})
                        current['revision'] = revision_re.match(out.next()).group(1)
                        m = dasl_re.match(out.next())
                        current['date'] = m.group(1)
                        current['author'] = m.group(2)
                        current['state'] = m.group(3)
                        current['comment'] = out.next().strip()
        return history
        
    def remove(self, paths):
        for path in paths:
            root = path
            if os.path.isdir(path):
                root = os.path.dirname(path)
            out = self.run(self.getWorkingDirectory(root), 
                           ['remove',os.path.basename(path)])
        
    def status(self, paths, recursive=False):
        """ Get SVN status information from given file/directory """
        status = {}
        codes = {' ':'uptodate', 'A':'added', 'C':'conflict', 'D':'deleted',
                 'M':'modified'}
        options = ['status', '-v']
        if not recursive:
            options.append('-N')
        for path in paths:
            out = self.run(self.getWorkingDirectory(path), 
                           options + self.getPathList([path]))
            if out:
                for line in out:
                    name = line.strip().split()[-1]
                    try: status[name] = {'status':codes[line[0]]}
                    except KeyError: pass
            #print status
        return status

    def update(self, paths):
        print paths
        for path in paths:
            root = path
            if os.path.isdir(path):
                root = os.path.dirname(path)
            out = self.run(self.getWorkingDirectory(root), 
                           ['update', os.path.basename(path)])
        
    def revert(self, paths):
        for path in paths:
            root = path
            if os.path.isdir(path):
                root = os.path.dirname(path)
            out = self.run(self.getWorkingDirectory(root), 
                           ['revert','-R',os.path.basename(path)])
               
if __name__ == '__main__':
    svn = SVN()
    svn.add(['/Users/kesmit/pp/editra-plugins/Projects/projects/Icons'])