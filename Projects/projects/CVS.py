#!/usr/bin/env python

import re, os
from SourceControl import SourceControl

class CVS(SourceControl):

    command = 'cvs'
    
    def isControlled(self, path):
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        return os.path.isdir(os.path.join(path,'CVS'))

    def addRootOption(self, directory, options):
        """ Add CVS root option """
        return options
        try: 
            root = open(os.path.join(directory,'CVS','Root')).read().strip()
            return ['-d',root] + list(options)
        except OSError: 
            pass
        return options        

    def add(self, paths):
        for path in paths:
            root, files = self.splitFiles(path, forcefiles=True)
            out = self.run(root, ['add'] + files)
            print out.read()
        
    def checkout(self, paths):
        for path in paths:
            root, files = self.splitFiles(path, forcefiles=True)
            out = self.run(root, ['checkout'] + files)
            print out.read()
            
    def commit(self, paths, message=''):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['commit', '-R', '-m', message] + files)
            print out.read()
            
    def diff(self, paths):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['diff'] + files)
            print out.read()
            
    def history(self, paths):
        history = []
        for path in paths:
            root, files = self.splitFiles(path)           
            out = self.run(root, ['rlog'] + files)
            if out:
                revision_re = re.compile(r'^revision\s+(\S+)')
                dasl_re = re.compile(r'^date:\s+(\S+\s+\S+);\s+author:\s+(\S+);\s+state:\s+(\S+);')
                for line in out:
                    print line,
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
            root, files = self.splitFiles(path, forcefiles=True, topdown=False)           
            out = self.run(root, ['remove'] + files)
            print out.read()
            
    def status(self, paths, recursive=False):
        status = {}
        rec = []
        if recursive:
            rec = ['-R']
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['status', '-l'] + rec + files)
            if out:
                status_re = re.compile(r'^File:\s+(\S+)\s+Status:\s+(.+?)\s*$')        
                rep_re = re.compile(r'^\s*Working revision:\s*(\S+)')        
                rrep_re = re.compile(r'^\s*Repository revision:\s*(\S+)')        
                tag_re = re.compile(r'^\s*Sticky Tag:\s*(\S+)')        
                date_re = re.compile(r'^\s*Sticky Date:\s*(\S+)')        
                options_re = re.compile(r'^\s*Sticky Options:\s*(\S+)')
                directory_re = re.compile(r'^cvs server: Examining (\S+)')
                dir = ''        
                for line in out:
                    print line,
                    if status_re.match(line):
                        m = status_re.match(line)
                        key, value = m.group(1), m.group(2) 
                        if dir and dir != '.':
                            key = os.path.join(dir, key)
                        value = value.replace('-','').replace(' ','').lower()
                        current = status[key] = {}
                        if 'modified' in value:
                            current['status'] = 'modified'
                        elif 'added' in value:
                            current['status'] = 'added'
                        elif 'uptodate' in value:
                            current['status'] = 'uptodate'
                        elif 'remove' in value:
                            current['status'] = 'deleted'
                        elif 'merge' in value:
                            current['status'] = 'conflict'
                    elif directory_re.match(line):
                        dir = directory_re.match(line).group(1)
                    elif rep_re.match(line):
                        current['revision'] = rep_re.match(line).group(1)
                    elif rrep_re.match(line):
                        current['rrevision'] = rrep_re.match(line).group(1)
                    elif tag_re.match(line):
                        current['tag'] = tag_re.match(line).group(1)
                        if current['tag'] == '(none)':
                            del current['tag']
                    elif date_re.match(line):
                        current['date'] = date_re.match(line).group(1)
                        if current['date'] == '(none)':
                            del current['date']
                    elif options_re.match(line):
                        current['options'] = options_re.match(line).group(1)
                        if current['options'] == '(none)':
                            del current['options']
        return status

    def update(self, paths):
        for path in paths:
            root, files = self.splitFiles(path)
            out = self.run(root, ['update','-R'] + files)
            print out.read()
            
    def revert(self, paths):
        for path in paths:
            root, files = self.splitFiles(path, forcefiles=True, type=self.TYPE_FILE)
            for file in files:
                out = self.run(root, ['checkout','-p'] + files)
                if out:
                    content = out.read() 
                    if not content.startswith('cvs server'):
                        open(path, 'w').write(content)
    
    def fetch(self, paths):
        output = []
        for path in paths:
            if os.path.isdir(path):
                continue
            root, files = self.splitFiles(path)
            out = self.run(root, ['checkout', '-p'] + files)
            if out:
                content = out.read() 
                if not content.startswith('cvs server'):
                    output.append(content)
                else:
                    output.append(None)
            else:
                output.append(None)
        return output
                        
if __name__ == '__main__':
    cvs = CVS()
    print cvs.status(['.'], recursive=True)
    print cvs.history(['/Users/kesmit/pp/resolve/ods/src/odscol.c'])