#!/usr/bin/env python

'''
A simple python module for creating images out of netcdf arrays and outputing
kml files for Google Earth.   The base class ncEarth cannot be used on its own,
it must be subclassed with certain functions overloaded to provide location and
plotting that are specific to a model's output files.

Requires matplotlib and netCDF4 python modules.

Use as follows:

import ncEarth
kml=ncEarth.ncEpiSim('episim_0010.nc')
kml.write_kml(['Susceptible','Infected','Recovered','Dead'])

or

kmz=ncEarth.ncWRFFire_mov('wrfout')
kmz.write('FGRNHFX','fire.kmz')

Author: Jonathan Beezley (jon.beezley@gmail.com)
Date: Oct 5, 2010

kmz=ncEarth.ncWRFFire_mov('wrfout')
kmz.write_preload('FGRNHFX')

Modified by Lin Zhang
Date: Dec 20, 2010
'''


from matplotlib import pylab
from matplotlib.colorbar import ColorbarBase
from matplotlib.colors import LogNorm,Normalize
from matplotlib.ticker import LogFormatter
import numpy as np
try:
    from netCDF4 import Dataset
except:
    from Scientific.IO.NetCDF import NetCDFFile as Dataset
import cStringIO
from datetime import datetime
import zipfile
import shutil,os
import warnings
warnings.simplefilter('ignore')

class ZeroArray(Exception):
    pass

class ncEarth(object):
    
    '''Base class for reading NetCDF files and writing kml for Google Earth.'''
    
    kmlname='ncEarth.kml'  # default name for kml output file
    progname='baseClass'   # string describing the model (overload in subclass)
    
    # base kml file format string
    # creates a folder containing all images
    kmlstr= \
    '''<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
    <Folder>
    <name>%(prog)s visualization</name>
    <description>Variables from %(prog)s output files visualized in Google Earth</description>
    %(content)s
    </Folder>
    </kml>'''

    # string for static Ground Overlays
    kmlimageStatic= \
    '''<GroundOverlay>
      <name>%(name)s</name>
      <color>00ffffff</color>
      <Icon>
        <href>%(filename)s</href>
        <viewBoundScale>0.75</viewBoundScale>
      </Icon>
      <altitude>0.0</altitude>
      <altitudeMode>clampToGround</altitudeMode>
      <LatLonBox>
        <north>%(lat2)f</north>
        <south>%(lat1)f</south>
        <east>%(lon2)f</east>
        <west>%(lon1)f</west>
        <rotation>0.0</rotation>
      </LatLonBox>
    </GroundOverlay>'''

    # format string for each image
    kmlimage= \
    '''<GroundOverlay>
      <name>%(name)s</name>
      <color>%(alpha)02xffffff</color>
      <Icon>
        <href>%(filename)s</href>
        <viewBoundScale>0.75</viewBoundScale>
      </Icon>
      <altitude>0.0</altitude>
      <altitudeMode>clampToGround</altitudeMode>
      <LatLonBox>
        <north>%(lat2)f</north>
        <south>%(lat1)f</south>
        <east>%(lon2)f</east>
        <west>%(lon1)f</west>
        <rotation>0.0</rotation>
      </LatLonBox>
      %(time)s
    </GroundOverlay>'''

    kmlcolorbar= \
    '''
<ScreenOverlay>
   <name>%(name)s colorbar</name>
   <color>ffffffff</color>
   <Icon>
      <href>%(file)s</href>
   </Icon>
   <overlayXY x=".15" y=".5" xunits="fraction" yunits="fraction"/>
   <screenXY x="0" y=".5" xunits="fraction" yunits="fraction"/>
   <rotationXY x="0" y="0" xunits="fraction" yunits="fraction"/>
   <size x="0" y=".75" xunits="fraction" yunits="fraction"/>
</ScreenOverlay> 
    '''
    
    # time interval specification for animated output
    timestr=\
    '''<TimeSpan>
    %(begin)s
    %(end)s
    </TimeSpan>'''
    
    beginstr='<begin>%s</begin>'
    endstr='<end>%s</end>'
    
    def __init__(self,filename,hsize=5):
        '''Class constructor:
           filename : string NetCDF file to read
           hsize : optional, width of output images in inches'''
        
        self.f=Dataset(filename,'r')
        self.hsize=hsize
        self.minmax={}

    def get_minmax(self,vname):
        if self.minmax.has_key(vname):
            return self.minmax[vname]
        v=self.f.variables[vname][:]
        self.minmax[vname]=(v.min(),v.max())
        return self.minmax[vname]
    
    def get_bounds(self):
        '''Return the latitude and longitude bounds of the image.  Must be provided
        by the subclass.'''
        raise Exception("Non-implemented base class method.")
    
    def get_array(self,vname):
        '''Return a given array from the output file.  Must be returned as a
        2D array with top to bottom orientation (like an image).'''
        v=self.f.variables[vname]
        v=pylab.flipud(v)
        return v
    
    def view_function(self,v):
        '''Any function applied to the image data before plotting.  For example,
        to show the color on a log scale.'''
        return v
    
    def get_image(self,v,min,max):
        '''Create an image from a given data.  Returns a png image as a string.'''
                
        # kludge to get the image to have no border
        fig=pylab.figure(figsize=(self.hsize,self.hsize*float(v.shape[0])/v.shape[1]))
        ax=fig.add_axes([0,0,1,1])
        
        cmap=pylab.cm.jet
        cmap.set_bad('w',0.)
        norm=self.get_norm(min,max)
        pylab.imshow(self.view_function(v),cmap=cmap,norm=norm)
        pylab.axis('off')
        self.process_image()
        
        # create a string buffer to save the file
        im=cStringIO.StringIO()
        pylab.savefig(im,format='png',transparent=True)
        
        # return the buffer
        s=im.getvalue()
        im.close()
        return s

    def get_colorbar(self,title,label,min,max):
        '''Create a colorbar from given data.  Returns a png image as a string.'''
        
        fig=pylab.figure(figsize=(2,5))
        ax=fig.add_axes([0.35,0.03,0.1,0.9])
        norm=self.get_norm(min,max)
        formatter=self.get_formatter()
        if formatter:
            cb1 = ColorbarBase(ax,norm=norm,format=formatter,spacing='proportional',orientation='vertical')
        else:
            cb1 = ColorbarBase(ax,norm=norm,spacing='proportional',orientation='vertical')
        cb1.set_label(label,color='1')
        ax.set_title(title,color='1')
        for tl in ax.get_yticklabels():
            tl.set_color('1')
        im=cStringIO.StringIO()
        pylab.savefig(im,dpi=300,format='png',transparent=True)
        s=im.getvalue()
        im.close()
        return s

    def get_norm(self,min,max):
        norm=Normalize(min,max)
        return norm

    def get_formatter(self):
        return None
    
    def process_image(self):
        '''Do anything to the current figure window before saving it as an image.'''
        pass
    
    def get_kml_dict(self,name,filename,alpha=143):
        '''returns a dictionary of relevant info the create the image
        portion of the kml file'''
        
        lon1,lon2,lat1,lat2=self.get_bounds()
        d={'lat1':lat1,'lat2':lat2,'lon1':lon1,'lon2':lon2, \
           'name':name,'filename':filename,'time':self.get_time(),'alpha':alpha}
        return d
    
    def get_time(self):
        '''Return the time interval information for this image using the kml
        format string `timestr'.  Or an empty string to disable animations.'''
        return ''

    def image2kmlStatic(self,varname,filename=None):
        '''Read data from the NetCDF file, create a psuedo-color image as a png,
        then create a kml string for displaying the image in Google Earth.  Returns
        the kml string describing the GroundOverlay.  Optionally, the filename
        used to write the image can be specified, otherwise a default will be used.'''
        
        vdata=self.get_array(varname)
        min,max=self.get_minmax(varname)
        im=self.get_image(vdata,min,max)
        if filename is None:
            filename='%s.png' % varname
        f=open(filename,'w')
        f.write(im)
        f.close()
        d=self.get_kml_dict(varname,filename)
        pylab.close('all')
        return self.__class__.kmlimageStatic % d

    def image2kml(self,varname,filename=None):
        '''Read data from the NetCDF file, create a psuedo-color image as a png,
        then create a kml string for displaying the image in Google Earth.  Returns
        the kml string describing the GroundOverlay.  Optionally, the filename
        used to write the image can be specified, otherwise a default will be used.'''
        
        vdata=self.get_array(varname)
        min,max=self.get_minmax(varname)
        im=self.get_image(vdata,min,max)
        if filename is None:
            filename='%s.png' % varname
        f=open(filename,'w')
        f.write(im)
        f.close()
        d=self.get_kml_dict(varname,filename)
        pylab.close('all')
        return self.__class__.kmlimage % d
    
    def colorbar2kml(self,varname,filename=None):
        min,max=self.get_minmax(varname)
        label=self.get_label(varname)
        cdata=self.get_colorbar(varname,label,min,max)
        if filename is None:
            filename='colorbar_%s.png' % varname
        f=open(filename,'w')
        f.write(cdata)
        f.close()
        pylab.close('all')
        return self.__class__.kmlcolorbar % {'name':varname,'file':filename}

    def get_label(self,varname):
        return ''
    
    def write_kml(self,varnames):
        '''Create the actual kml file for a list of variables by calling image2kml
        for each variable in a list of variable names.'''
        if type(varnames) is str:
            varnames=(varnames,)
        content=[]
        for varname in varnames:
            label=self.get_label(varname)
            content.append(self.image2kml(varname))
            content.append(self.colorbar2kml(varname))
        kml=self.__class__.kmlstr % \
                     {'content':'\n'.join(content),\
                      'prog':self.__class__.progname}
        f=open(self.__class__.kmlname,'w')
        f.write(kml)
        f.close()

class ncEarth_log(ncEarth):
    def view_function(self,v):
        if v.max() <= 0.:
            raise ZeroArray()
        v=np.ma.masked_equal(v,0.,copy=False)
        v.fill_value=np.nan
        v=np.log(v)
        return v

    def get_norm(self,min,max):
        return LogNorm(min,max)

    def get_formatter(self):
        return LogFormatter(10,labelOnlyBase=False)

    def get_minmax(self,vname):
        if self.minmax.has_key(vname):
            return self.minmax[vname]
        v=self.f.variables[vname][:]
        if v[v>0].size == 0:
            min=1e-6
            max=1.
        else:
            min=v[v>0].min()
            max=v.max()
        self.minmax[vname]=(min,max)
        return self.minmax[vname]

class ncEpiSimBase(object):
    '''Epidemic model file class.'''
    
    kmlname='epidemic.kml'
    progname='EpiSim'
    
    def get_bounds(self):
        '''Get the lat/lon bounds of the output file... assumes regular lat/lon (no projection)'''
        lat=self.f.variables['latitude']
        lon=self.f.variables['longitude']
        
        lat1=lat[0]
        lat2=lat[-1]
        lon1=lon[0]
        lon2=lon[-1]
        
        return (lon1,lon2,lat1,lat2)
    
class ncEpiSim(ncEpiSimBase,ncEarth_log):
    pass

class ncWRFFireBase(object):
    '''WRF-Fire model file class.'''
    
    kmlname='fire.kml'
    progname='WRF-Fire'
    wrftimestr='%Y-%m-%d_%H:%M:%S'
    
    def __init__(self,filename,hsize=5,istep=0):
        '''Overloaded constructor for WRF output files:
           filename : output NetCDF file
           hsize : output image width in inches
           istep : time slice to output (between 0 and the number of timeslices in the file - 1)'''
        ncEarth.__init__(self,filename,hsize)
        self.istep=istep
    
    def get_bounds(self):
        '''Get the latitude and longitude bounds for an output domain.  In general,
        we need to reproject the data to a regular lat/lon grid.  This can be done
        with matplotlib's BaseMap module, but is not done here.'''
        
        lat=self.f.variables['XLAT'][0,:,:].squeeze()
        lon=self.f.variables['XLONG'][0,:,:].squeeze()
        dx=lon[0,1]-lon[0,0]
        dy=lat[1,0]-lat[0,0]
        #lat1=np.min(lat)-dy/2.
        #lat2=np.max(lat)+dy/2
        #lon1=np.min(lon)-dx/2.
        #lon2=np.max(lon)+dx/2
        lat1=lat[0,0]-dy/2.
        lat2=lat[-1,0]+dy/2.
        lon1=lon[0,0]-dx/2.
        lon2=lon[0,-1]+dx/2.
        return (lon1,lon2,lat1,lat2)
    
    def isfiregrid(self,vname):
        xdim=self.f.variables[vname].dimensions[-1]
        return xdim[-7:] == 'subgrid'

    def srx(self):
        try:
            s=len(self.f.dimensions['west_east_subgrid'])/(len(self.f.dimensions['west_east'])+1)
        except:
            s=(self.f.dimensions['west_east_subgrid'])/((self.f.dimensions['west_east'])+1)
        return s

    def sry(self):
        try:
            s=len(self.f.dimensions['south_north_subgrid'])/(len(self.f.dimensions['south_north'])+1)
        except:
            s=(self.f.dimensions['south_north_subgrid'])/((self.f.dimensions['south_north'])+1)
        return s

    def get_array(self,vname):
        '''Return a single time slice of a variable from a WRF output file.'''
        v=self.f.variables[vname]
        v=v[self.istep,:,:].squeeze()
        if self.isfiregrid(vname):
            v=v[:-self.sry(),:-self.srx()]
        v=pylab.flipud(v)
        return v
    
    def get_time(self):
        '''Process the time information from the WRF output file to create a
        proper kml TimeInterval specification.'''
        start=''
        end=''
        time=''
        g=self.f
        times=g.variables["Times"]
        if self.istep > 0:
            start=ncEarth.beginstr % \
               datetime.strptime(times[self.istep,:].tostring(),\
                                     self.__class__.wrftimestr).isoformat()
        if self.istep < times.shape[0]-1:
            end=ncEarth.endstr % \
               datetime.strptime(times[self.istep+1,:].tostring(),\
                                     self.__class__.wrftimestr).isoformat()
        if start is not '' or end is not '':
            time=ncEarth.timestr % {'begin':start,'end':end}
        return time

    def get_label(self,varname):
        v=self.f.variables[varname]
        return v.units

class ncWRFFire(ncWRFFireBase,ncEarth):
    pass

class ncWRFFireLog(ncWRFFireBase,ncEarth_log):
    pass

class ncWRFFire_mov(object):
    
    '''A class the uses ncWRFFire to create animations from WRF history output file.'''
    
    def __init__(self,filename,hsize=5,nstep=None):
        '''Class constructor:
           filename : NetCDF output file name
           hsize : output image width in inces
           nstep : the number of frames to process (default all frames in the file)'''
        
        self.filename=filename
        f=Dataset(filename,'r')
        g=f
        self.nstep=nstep
        if nstep is None:
            # in case nstep was not specified read the total number of time slices from the file
            self.nstep=g.variables['Times'].shape[0]

    def write_preload(self,vname,kmz='fire_preload.kmz'):
        '''Create a kmz file from multiple time steps of a wrfout file. The kml file consists of a set of 
        GroundOverlays with time tag and a copy of the set without the time tag to preload the
        images that are used in the GroundOverlays.'''
        
        
        imgs=[]     # to store a list of all images created
        content=[]  # the content of the main kml
        vstr='files/%s_%05i.png' # format specification for images (all stored in `files/' subdirectory)
        
        # create empty files subdirectory for output images
        try:
            shutil.rmtree('files')
        except:
            pass
        os.makedirs('files')
        
        # loop through all time slices and create the image data
        # appending to the kml content string for each image
        for i in xrange(0,self.nstep,1):
            print i
            kml=ncWRFFire(self.filename,istep=i)
            img=vstr % (vname,i)
            imgs.append(img)
            content.append(kml.image2kmlStatic(vname,img))
            kml.f.close()
        
        # create the main kml file
        kml=ncWRFFire.kmlstr % \
            {'content':'\n'.join(content),\
             'prog':ncWRFFire.progname}
        
        # create a zipfile to store all images + kml into a single compressed file
        z=zipfile.ZipFile(kmz,'w',compression=zipfile.ZIP_DEFLATED)
        z.writestr(kmz[:-3]+'kml',kml)
        for img in imgs:
            z.write(img)
        z.close()

    def write(self,vname,kmz='fire.kmz',hsize=5,logscale=True,colorbar=True):
        '''Create a kmz file from multiple time steps of a wrfout file.
        vname : the variable name to visualize
        kmz : optional, the name of the file to save the kmz to'''
        
        imgs=[]     # to store a list of all images created
        content=[]  # the content of the main kml
        vstr='files/%s_%05i.png' # format specification for images (all stored in `files/' subdirectory)
        
        # create empty files subdirectory for output images
        try:
            shutil.rmtree('files')
        except:
            pass
        os.makedirs('files')
        
        # loop through all time slices and create the image data
        # appending to the kml content string for each image
        k=0
        for i in xrange(0,self.nstep,1):
            if logscale:
                kml=ncWRFFireLog(self.filename,istep=i)
            else:
                kml=ncWRFFire(self.filename,istep=i)
            try:
                img=vstr % (vname,i)
                content.append(kml.image2kml(vname,img))
                imgs.append(img)
                print 'creating frame %i of %i' % (i,self.nstep)
                k=k+1
            except ZeroArray:
                print 'skipping frame %i of %i' % (i,self.nstep)
                pass
        if colorbar and k>0:
            img='files/colorbar_%s.png' % vname
            content.append(kml.colorbar2kml(vname,img))
            imgs.append(img)

        # create the main kml file
        kml=ncWRFFire.kmlstr % \
            {'content':'\n'.join(content),\
             'prog':ncWRFFire.progname}
        
        # create a zipfile to store all images + kml into a single compressed file
        z=zipfile.ZipFile(kmz,'w',compression=zipfile.ZIP_DEFLATED)
        z.writestr(kmz[:-3]+'kml',kml)
        for img in imgs:
            z.write(img)
        z.close()

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
