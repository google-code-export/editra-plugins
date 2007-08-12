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
            root, files = self.splitFiles(path)
            out = self.run(root, ['add'] + files)
            self.logOutput(out)
        
    def checkout(self, paths):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['checkout'] + files)
            self.logOutput(out)
        
    def commit(self, paths, message=''):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['commit', '-m', message] + files)
            self.logOutput(out)
                                   
    def diff(self, paths):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['diff'] + files)
            self.closeProcess(out)
        
    def history(self, paths):
        history = []
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['log'] + files)
            self.logOutput(out)
        return history
        
    def remove(self, paths):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['remove'] + files)
            self.logOutput(out)
        
    def status(self, paths, recursive=False):
        """ Get SVN status information from given file/directory """
        status = {}
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
                    name = line.strip().split()[-1]
                    try: status[name] = {'status':codes[line[0]]}
                    except KeyError: pass
                self.logOutput(out)
        return status

    def update(self, paths):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['update'] + files)
            self.logOutput(out)
            
    def revert(self, paths):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['revert','-R'] + files)
            self.logOutput(out)
            
    def fetch(self, paths):
        output = []
        for path in paths:
            if os.path.isdir(path):
                continue
            root, files = self.splitFiles(path)
            out = self.run(root, ['cat'] + files)
            if out:
                output.append(out.stdout.read())
                self.logOutput(out)
            else:
                output.append(None)
        return output
               
if __name__ == '__main__':
    svn = SVN()
    svn.add(['/Users/kesmit/pp/editra-plugins/Projects/projects/Icons'])