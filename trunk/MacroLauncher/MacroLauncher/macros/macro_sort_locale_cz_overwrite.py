# -*- coding: utf-8 -*-

name = 'sort-example'
type = 'example'
desc = 'Sort lines by Czech locale'

import locale

def run(txtctrl = None, **kwargs):
    locale.setlocale(locale.LC_ALL,"cz")
    if txtctrl:
        lines = txtctrl.GetText().splitlines()
        lines.sort(cmp=locale.strcoll)
        txtctrl.SetText(txtctrl.GetEOLChar().join(lines))
