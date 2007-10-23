#!/usr/bin/env python

import re, os, datetime
from SourceControl import SourceControl

class CVS(SourceControl):

    name = 'CVS'
    command = 'cvs'
    
    def __repr__(self):
        return 'CVS.CVS()'
    
    def getRepository(self, path):
        if not self.isControlled(path):
            return
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        repfile = os.path.join(path, 'CVS', 'Root')
        if not os.path.isfile(repfile):
            return
        return open(repfile, 'r').read().strip()
    
    def isControlled(self, path):
        """ Is the path controlled by CVS? """
        if os.path.isdir(path):
            if os.path.isfile(os.path.join(path,'CVS','Entries')):
                return True
        path, basename = os.path.split(path)
        cvsdir = os.path.join(path,'CVS')
        if os.path.isdir(cvsdir):
            try:
                for line in open(os.path.join(cvsdir,'Entries')):
                    if '/' not in line:
                        continue
                    type, filename, therest = line.split('/', 2)
                    if filename == basename:
                        return True
            except (IOError, OSError):
                pass
        return False

    def add(self, paths):
        root, files = self.splitFiles(paths, forcefiles=True)
        dirs = sorted([x for x in files if os.path.isdir(x)])
        files = sorted([x for x in files if not os.path.isdir(x)])
        # Add all directories individually first
        for d in dirs:
            droot = root
            if d == '.':
                droot, d = os.path.split(droot)
                if not d:
                    droot, d = os.path.split(droot)                
            out = self.run(droot, ['add', d])
            self.logOutput(out)
        # Add all files
        if files:
            out = self.run(root, ['add'] + files)
            self.logOutput(out)                
        
    def checkout(self, paths):
        root, files = self.splitFiles(paths, forcefiles=True)
        out = self.run(root, ['checkout'] + files)
        self.logOutput(out)
            
    def commit(self, paths, message=''):
        """ Commit all files with message """
        root, files = self.splitFiles(paths)
        out = self.run(root, ['commit', '-R', '-m', message] + files)
        self.logOutput(out)
            
    def diff(self, paths):
        root, files = self.splitFiles(paths)
        out = self.run(root, ['diff'] + files)
        self.logOutput(out)
            
    def history(self, paths, history=None):
        if history is None:
            history = []
        root, files = self.splitFiles(paths)
        for i, file in enumerate(files):
            rep = open(os.path.join(root, 'CVS', 'Repository')).read().strip()
            files[i] = os.path.join(rep, file)
        for file in files:
            out = self.run(root, ['rlog', file])
            if out:
                revision_re = re.compile(r'^revision\s+(\S+)')
                dasl_re = re.compile(r'^date:\s+(\S+\s+\S+);\s+author:\s+(\S+);\s+state:\s+(\S+);')
                current = None
                for line in out.stdout:
                    self.log(line)
                    if line.startswith('----------'):
                        current = {'path':file}
                        history.append(current)
                        line = out.stdout.next()
                        self.log(line)
                        current['revision'] = revision_re.match(line).group(1)
                        current['sortkey'] = [int(x) for x in current['revision'].split('.')]
                        line = out.stdout.next()
                        self.log(line)
                        m = dasl_re.match(line)
                        current['date'] = self.str2datetime(m.group(1))
                        current['author'] = m.group(2)
                        current['state'] = m.group(3)
                        line = out.stdout.next()
                        self.log(line)
                        current['log'] = line
                    elif line.startswith('========'):
                        current = None
                    elif current is not None:
                        current['log'] += line
                self.logOutput(out)
        history.sort(key=lambda x:x['sortkey'])
        history.reverse()
        return history
        
    def remove(self, paths):
        """ Recursively remove paths from source control """
        # Reverse paths so that files get deleted first
        for path in reversed(sorted(paths)):
            root, files = self.splitFiles(path)
            out = self.run(root, ['remove', '-R', '-f'] + files)
            self.logOutput(out)
            
    def status(self, paths, recursive=False, status={}):
        """
        Get the status of all given paths
        
        Required Arguments:
        paths -- list of paths to get the status of
        
        Keyword Arguments:
        recursive -- boolean indicating if the status should be recursive
        status -- dictionary containing status information.  This value
            is also the return value
        
        """
        rec = []
        if recursive:
            rec = ['-R']
        root, files = self.splitFiles(paths)
        out = self.run(root, ['status', '-l'] + rec + files, mergeerr=True)
        if out:
            status_re = re.compile(r'^File:\s+(\S+)\s+Status:\s+(.+?)\s*$')        
            rep_re = re.compile(r'^\s*Working revision:\s*(\S+)')        
            rrep_re = re.compile(r'^\s*Repository revision:\s*(\S+)')        
            tag_re = re.compile(r'^\s*Sticky Tag:\s*(\S+)')        
            date_re = re.compile(r'^\s*Sticky Date:\s*(\S+)')        
            options_re = re.compile(r'^\s*Sticky Options:\s*(\S+)')
            directory_re = re.compile(r'^cvs server: Examining (\S+)')
            dir = ''        
            for line in out.stdout:
                self.log(line)
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
                    elif 'conflict' in value:
                        current['status'] = 'conflict'
                    elif 'merge' in value:
                        current['status'] = 'merge'
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
            self.logOutput(out)
        return status
    
    def str2datetime(self, s):
        return datetime.datetime(*[int(x) for x in re.split(r'[\s+/:]', s.strip()) if x])

    def update(self, paths):
        """ Recursively update paths """
        root, files = self.splitFiles(paths)
        out = self.run(root, ['update','-R'] + files)
        self.logOutput(out)
            
    def revert(self, paths): 
        """ Revert paths to repository versions """
        for path in paths:
            root, files = self.splitFiles(path, forcefiles=True, type=self.TYPE_FILE)
            for file in files:
                out = self.fetch([os.path.join(root,file)])[0]
                if out is not None:
                    open(os.path.join(root,file), 'w').write(out)
    
    def fetch(self, paths, rev=None, date=None):
        """ Fetch a copy of the paths from the repository """
        output = []
        for path in paths:
            if os.path.isdir(path):
                continue
            root, files = self.splitFiles(path)
            for i, file in enumerate(files):
                rep = open(os.path.join(root, 'CVS', 'Repository')).read().strip()
                files[i] = os.path.join(rep, file)
                
            options = []
            if rev:
                options.append('-r')
                options.append(rev)
            if date:
                options.append('-D')
                options.append(date)            
            
            out = self.run(root, ['checkout', '-p'] + options + files)
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
    cvs = CVS()
    print cvs.status(['.'], recursive=True)
    print cvs.history(['/Users/kesmit/pp/resolve/ods/src/odscol.c'])
