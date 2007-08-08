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
            print out.read()
        
    def checkout(self, paths):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['checkout'] + files)
            print out.read()
        
    def commit(self, paths, message=''):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['commit', '-m', message] + files)
            print out.read()
                                   
    def diff(self, paths):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['diff'] + files)
        
    def history(self, paths):
        history = []
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['log'] + files)
            print out.read()
        return history
        
    def remove(self, paths):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['remove'] + files)
            print out.read()
        
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
                for line in out:
                    print line,
                    name = line.strip().split()[-1]
                    try: status[name] = {'status':codes[line[0]]}
                    except KeyError: pass
            #print status
        return status

    def update(self, paths):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['update'] + files)
            print out.read()
            
    def revert(self, paths):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['revert','-R'] + files)
            print out.read()
            
    def fetch(self, paths):
        output = []
        for path in paths:
            if os.path.isdir(path):
                continue
            root, files = self.splitFiles(path)
            out = self.run(root, ['cat'] + files)
            if out:
                output.append(out.read())
            else:
                output.append(None)
        return output
               
if __name__ == '__main__':
    svn = SVN()
    svn.add(['/Users/kesmit/pp/editra-plugins/Projects/projects/Icons'])