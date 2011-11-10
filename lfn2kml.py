#!/usr/bin/env python

import matplotlib
try:
    matplotlib.use('Agg')
except:
    pass

from netCDF4 import Dataset
from pylab import contour
import sys

kmlstr= \
'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>fire_perimeter.kml</name>
      <Style id="redLine">
        <LineStyle>
            <color>ff0000ff</color>
            <width>3</width>
        </LineStyle>
        <PolyStyle>
            <color>ff0000ff</color>
            <fill>0</fill>
        </PolyStyle>
      </Style>
  <open>0</open>
  %s
</Document>
</kml>'''
placestr= \
'''<Placemark>
    <name>Fire perimeter at %(time)s</name>
    <styleUrl>#redLine</styleUrl>
    <MultiGeometry>
    %(poly)s
    </MultiGeometry>
  </Placemark>'''

polystr= \
'''<Polygon>
      <tessellate>1</tessellate>
      <altitudeMode>clampToGround</altitudeMode>
      <outerBoundaryIs>
        <LinearRing>
          <coordinates>
           %s
          </coordinates>
        </LinearRing>
      </outerBoundaryIs>
    </Polygon>'''

def getpts(file,nstep=-1):
    f=Dataset(file,'r')
    if f.variables['LFN'].shape[0] == 1:
        lfn=f.variables['LFN'][0,:,:]
    else:
        lfn=f.variables['LFN'][n,:,:]
    
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
    return poly

def gettime(file,nstep=-1):
    f=Dataset(file,'r')
    if len(f.variables['Times']) == 1:
        t=f.variables['Times'][0].tostring()
    else:
        t=f.variables['Times'][n].tostring()
    return t

def createkml(poly,time):
    l=[]
    for p in poly:
       l.append(createpoly(p))
    s='\n'.join(l)
    s=placestr % {'time':time, 'poly':s}
    return kmlstr % s

def createpoly(poly):
    l=[]
    for i in xrange(poly.shape[0]):
        l.append('%f,%f' % (poly[i,0],poly[i,1]))
    s='\n'.join(l)
    return polystr % s

def main(file,nstep=-1):
    time=gettime(file,nstep)
    poly=getpts(file,nstep)
    s=createkml(poly,time)
    f=open('fire_perimeter.kml','w')
    f.write(s)

'''    
def main(argv):
    import shapefile
    if len(sys.argv[1:]) > 1:
        n=int(sys.argv[2])
    else:
        n=-1
    poly=getpts(argv[1],n) 
    w=shapefile.Writer(shapeType=shapefile.POLYGON)
    w.poly(parts=poly)
    w.save('fire.shp')
    
    sys.exit(0)
'''


if __name__ == '__main__':
    if len(sys.argv[1:]) > 1:
        n=int(sys.argv[2])
    else:
        n=-1
    main(sys.argv[1],n)
