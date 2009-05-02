
# -*- coding: utf-8 -*-

name = u'thread1'
type = u'example'
desc = u'Fast thread that prints into log - select both and right-click to run'

import time

def run_thread(log=None, **kwargs):
  for x in range(50):
      time.sleep(.1)
      log('thread1 printing')
      yield 
