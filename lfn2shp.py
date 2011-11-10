#!/usr/bin/env python

import matplotlib
try:
    matplotlib.use('Agg')
except:
    pass

from netCDF4 import Dataset
from pylab import contour
import shapefile
import sys

f=Dataset(sys.argv[1],'r')
if len(sys.argv[1:]) > 1:
    n=int(sys.argv[2])
    lfn=f.variables['LFN'][n,:,:]
else:
    lfn=f.variables['LFN'][0,:,:]


(fny,fnx)=lfn.shape
nx=len(f.dimensions['west_east'])+1
ny=len(f.dimensions['south_north'])+1

(srx,sry)=(fnx/nx,fny/ny)

lfn=lfn[:-sry,:-srx]

if (lfn > 0).all():
    sys.exit(1)

x=f.variables['FXLONG'][0,:-sry,:-srx]
y=f.variables['FXLAT'][0,:-sry,:-srx]
c=contour(x,y,lfn,[0]).collections[0]

p=c.get_paths()
poly=[]
for i in p:
    poly.extend(i.to_polygons())
w=shapefile.Writer(shapeType=shapefile.POLYGON)
w.poly(parts=poly)
w.save('fire.shp')

sys.exit(0)
