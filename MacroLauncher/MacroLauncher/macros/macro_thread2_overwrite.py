
# -*- coding: utf-8 -*-

name = u'thread2'
type = u'example'
desc = u'Slower thread that prints into log - select both and right-click to run'

import time

def run_thread(log=None, **kwargs):
  for x in range(25):
      time.sleep(.2)
      log('thread2 printing')
      yield 
