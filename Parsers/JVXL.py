if __name__ == "__main__":
    import sys,os
    selfname = sys.argv[0]
    full_path = os.path.abspath(selfname)[:]
    last_slash = full_path.rfind('/')
    dirpath = full_path[:last_slash] + '/..'
    print "Append to PYTHONPATH: %s" % (dirpath)
    sys.path.append(dirpath)

import logging
import shutil
from Top import Top
import Tools.web as web
from Geometry import ListGeoms,Geom
from Parsers.XYZ import XYZ
from Tools.IO import is_readable
log = logging.getLogger(__name__)


class JVXL(Top):
    """
    What are we going to do with JVXL:
        1. show .{jvxl,xyz} files.
            In this case, we just copy them to terse-pics/ and make appropriate links
        2. Save any isosurface as terse-pics/.{jvxl,xyz} to reduce I/O
            * Currently, we work with isosurfaces only via .cube files.
                * Therefore, we need a convertor of .cube to .jvxl
                    * It should be implemented as a method of .cube
                    * Besides, .jvxl does not contain geometry
                        * We also need to save geometry
    How to do it:
        * We need a cube file to produce isosurface
        * We need to run Jmol in stand-alone mode to convert cube to .{jvxl,cube}
    """
    def __init__(self):
        self.fileJ = ''
        self.fileX = ''
        self.X = XYZ()
        self.wp = '' # web path to the file


    def LookUpByBasename(self,extension='.xyz'):
        lastDot = self.fileJ.rfind('.')
        return self.fileJ[:lastDot] + extension


    def parse(self,WebPath='',ToBeCopied = True):
        # Check if .jvxl is readable
        if not 'j' in self.file:
            log.error('JVXL file is needed')
            return
        self.fileJ = self.file['j']
        if not is_readable(self.fileJ):
            log.warning('JVXL file is not readable')
            return

        # Parse XYZ File
        if 'x' in self.file:
            self.fileX = self.file['x']
        else:
            log.debug('XYZ file name is not provided in the input; trying to guess...')
            self.fileX = self.LookUpByBasename()
        if is_readable(self.fileX):
            log.debug('XYZ file found: %s' % (self.fileX))
        else:
            log.warning('XYZ file is not readable')
            return
        self.X.file = self.fileX
        self.X.parse()

        # Copy JVXL file
        rp = self.settings.realPath('.jvxl')
        shutil.copy(self.fileJ,rp)
        self.wp = self.settings.webPath('.jvxl')



    def webData(self):
        """
        Makes HTML row.
        return: b1,b2
        """

        we = self.settings.Engine3D()

        wp_xyz = self.X.geoms.write(fname='.xyz')
        b1 = we.JMolApplet(webpath = wp_xyz)

        iso_on = we.JMol_JVXL(webpath = self.wp)
        iso_off = 'isosurface off'
        b2 = we.JMolButton(iso_on,label='Isosurface On') + we.JMolButton(iso_off,label='Off')

        log.debug('webData generated successfully')
        return b1, b2


#
#
#
#
#
if __name__ == "__main__":

    DebugLevel = logging.DEBUG
    logging.basicConfig(level=DebugLevel)

    from Settings import Settings
    Top.settings = Settings(FromConfigFile = True)

    """
    f = Cube(file=sys.argv[1])
    f.extractXYZ()
    f.processFiles()

    from HTML import HTML
    WebPage = HTML()
    WebPage.makeHeader()
    b1,b2 = f.webData()
    WebPage.makeLine(b1,b2)
    WebPage.makeTail()
    WebPage.write()
    """
