#!/usr/bin/env python

'''
Driver script for converting WRF-Fire netcdf output file to a sequence of kml
for use with Google maps.

Usage: nc2kml_sequence.py filename [var1 [var2 ...]]
'''

from ncEarth import ncWRFFire,ncWRFFireLog,ZeroArray
from netCDF4 import Dataset
import sys
import os
import shutil

kmlpath='kml'
filepath='files'

def uselog(vname):
    if vname in ('FGRNHFX','GRNHFX'):
        return True
    else:
        return False

def getTimes(file):
    f=Dataset(file,'r')
    t=f.variables['Times'][:]
    t=[t[i,:].tostring() for i in range(t.shape[0])]
    return t

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
        #kmz=ncWRFFire_mov(filename)
        times=getTimes(filename)
        n=0
        try:
            shutil.rmtree(kmlpath)
        except Exception:
            pass
        os.mkdir(kmlpath)
        for time in times:
            n=n+1
            fname=os.path.join(kmlpath,'WRF-Fire_%03i.kml'%n)
            print 'Creating %s.' % fname
            if uselog(vars[0]):
                foo=ncWRFFireLog
            else:
                foo=ncWRFFire

            kml=foo(filename,istep=n-1)
            try:
                kml.write_kml(vars,kmlfile=fname,imgfile=os.path.join(filepath,'img_%03i.png' % n),colorbar=False)
            except ZeroArray:
                pass
