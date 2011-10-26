#!/usr/bin/env python

'''
Driver script for converting WRF-Fire netcdf output file to kmz.  

Usage: nc2kmz.py filename [var1 [var2 ...]]
'''

from ncEarth import ncWRFFire_mov
import sys

def uselog(vname):
    if vname in ('FGRNHFX','GRNHFX'):
        return True
    else:
        return False

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print "Takes a WRF-Fire output file and writes fire.kmz."
        print "usage: %s filename"%sys.argv[0]
    else:
        filename=sys.argv[1]
        if len(sys.argv) == 2:
            vars=('FGRNHFX',)
        else:
            vars=sys.argv[2:]
        kmz=ncWRFFire_mov(filename)
        for v in vars:
            kmz.write(v,hsize=8,kmz='fire_'+v+'.kmz',logscale=uselog(v))
