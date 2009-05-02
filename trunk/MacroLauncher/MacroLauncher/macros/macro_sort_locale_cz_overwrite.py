
# -*- coding: utf-8 -*-

name = 'sort-example'
type = 'example'
desc = 'Sort lines by Czech locale'

import locale
locale.setlocale(locale.LC_ALL,"cz")



def run(txtctrl = None, **kwargs):
  if txtctrl:
    lines = txtctrl.GetText().splitlines()
    lines.sort(cmp=locale.strcoll)
    txtctrl.SetText(txtctrl.GetEOLChar().join(lines))
