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
    %(timestr)s
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

# time interval specification for animated output
timestr=\
'''<TimeSpan>
%(begin)s
%(end)s
</TimeSpan>'''
    
beginstr='<begin>%s</begin>'
endstr='<end>%s</end>'
wrftimestr='%Y-%m-%d_%H:%M:%S'

def getpts(file,nstep=-1):
    f=Dataset(file,'r')
    if f.variables['LFN'].shape[0] == 1:
        lfn=f.variables['LFN'][0,:,:]
    else:
        lfn=f.variables['LFN'][nstep,:,:]
    
    (fny,fnx)=lfn.shape
    nx=len(f.dimensions['west_east'])+1
    ny=len(f.dimensions['south_north'])+1
    
    (srx,sry)=(fnx/nx,fny/ny)
    
    lfn=lfn[:-sry,:-srx]
    
    if (lfn > 0).all():
        return None
    
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
    if nstep >= len(f.variables['Times']):
        return ''
    if len(f.variables['Times']) == 1:
        t=f.variables['Times'][0].tostring()
    else:
        t=f.variables['Times'][nstep].tostring()
    return t.replace('_','T')

def createkml(poly,time,tstr):
    l=[]
    for p in poly:
       l.append(createpoly(p,tstr))
    s='\n'.join(l)
    s=placestr % {'time':time, 'poly':s, 'timestr':tstr}
    return s #kmlstr % s

def createpoly(poly,time=''):
    l=[]
    for i in xrange(poly.shape[0]):
        l.append('%f,%f' % (poly[i,0],poly[i,1]))
    s='\n'.join(l)
    return polystr % s

def main(file,nstep=None):
    last=False
    only=True
    s=[]
    if nstep is None:
        nstep=0
        only=False
    while not last:
        time=gettime(file,nstep)
        stime=time
        etime=gettime(file,nstep+1)
       if etime=='':
            etime=stime
            last=True
        sstime=beginstr % stime
        setime=endstr % etime
        tstr=timestr % {'begin':sstime,'end':setime}
        poly=getpts(file,nstep)
       if poly is not None:
            s.append(createkml(poly,time,tstr))
        nstep=nstep+1
        if only:
            last=True
    s='\n'.join(s)
    s=kmlstr % s
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
        n=None
    main(sys.argv[1],n)
