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
import os
from Top import Top
import Tools.web as web
from Geometry import ListGeoms,Geom
from Parsers.JVXL import JVXL
from Tools.IO import RunJmol
import re
log = logging.getLogger(__name__)


class Cube(Top):
    """
    Shows 3D-properties from the .cube file

    How to do it:
        1) Specify the file name
        2) Specify the isosurface value to be plot (or give choice via UI elements)
        3) If we have .cube file somewhere else than terse-pics, then make a copy in terse-pics
        .) Read XYZ coordinates from the cube file
        .) Generate HTML code for XYZ coordinates
        4) Generate HTML code to put into b1
        5) In b2, make a checkbox

    In perspective, we might want to plot several surfaces in one JmolApplet (simultaneously or only one at time).

    How are we going to use it?
        [V] U1) Show single .cube file content (here, we use terse as a .cube file parser)
        U2) Parse .fchk file: extract selected/all properties and show them. In this case, we will
            need to load JmolApplet and XYZ file once, and use UI elements to choose properties of interest and isosurface values
        U3) Show NBO interactions. We will need text parser to find orbital interactions (from Gaussian output), and show them
            by pairs of orbitals (donor/acceptor).
        U4) Show TD-DFT transitions. If we use natural transition orbitals (BTW what are they?), then we probably would have
            to show list of orbitals. If we parse excited state compositions from Gaussian output, then we again would have
            list of pairs of orbitals (for each excited state, dominant transition should be shown in the form of from-->to orbitals).

    How are we going to realize it?
        1) Eventually, for each property, we will need to plot an isosurface, so Cube should have a function which returns
            a Jmol script line that loads isosurface in the existing Jmol window
        2) .webData function should solve problem U1
        3) Problem U2 should be solved via FchkGaussian class (it would be cool to parse FchkGaussin, as it has a lot of
            information about the calculations, so we can show geometries, freqs, charges, and other properties as well
            as Electrostatic potentials and other space-distributed properties
        4) For problem U3, special class should be created, which will be activated by command-line options
            (because only specific Gaussian input files can generate .fchk with NBO orbitals; and both .chk and .log files should be provided)
        5) To solve U4, we need both .log and .chk files, so it should be a special kind of input for terse.py.
            Probably, there is no other special reasons for not to show these things by default.
        *) What we can do: add a global key that allows to look up for .chk file (from Gaussian log file or just by assuming that 
            chk file has the same basename as the log file)

    Notes:
        1) ESP should be treated in a special way, as it needs density cube and ESP cube
        2) What about showing ESP critical points on the ESP isodensity surface? (though, is not it too complicated and out of scope of this program?)
        3) It's trivial to combine cubes! (multiply,divide,sum,substract and so on)

    OK, so what's the plan?
        [V] 1) Cube should be just a helper class with few functions:
            [V] ) extract molecular XYZ;
            [V] ) generate scipt for Jmol to show isosurface with a given isovalue
            [V] ) 'parse' single .cube files (like we do it with .xyz and Gau);
        So, I can start with implementing this functionality
        2) Solve U2. I will plan it a little later

    """
    def __init__(self,name='',colors=''):
        self.geom = Geom() # geom extracted from the cube
        self.wpcube = '' # web path to the .cube
        self.name = name
        self.colors = colors
        self.isotype = ''
        self.isovalue = '0.03'


    def parse(self):
        self.extractXYZ()

        if not self.wpcube: # A trick: if self.wpcube is given, we don't copy file
            rp = self.settings.realPath('.cube')
            self.wpcube = self.settings.webPath('.cube')
            shutil.copy(self.file,rp)
            self.file = rp

        """
        Normally, this kind of things are defined in webData,
        but we need to do it here, because it might be redefined
        by make_JVXL; and it would be uglier to put make_JVXL
        into webData
        """
        we = self.settings.Engine3D()
        if self.settings.useJVXL:
            self.s_script = we.JMolIsosurface(webpath = self.file,isovalue=self.isovalue,surftype=self.isotype,use_quotes=True,name=self.name,colors=self.colors)
            self.J = self.make_JVXL()
            if not self.settings.save_cube:
                os.remove(self.file)
        else:
            self.s_script = we.JMolIsosurface(webpath = self.wpcube,name=self.name,colors=self.colors)



    def extractXYZ(self):
        Bohr = 0.52917721

        try:
            FI = open(self.file)
            log.debug('%s was opened for reading' %(self.file))
        except:
            log.error('Cannot open %s for reading' %(self.file))

        comment1 = FI.readline()
        comment2 = FI.readline()

        line3 = FI.readline().split()
        natoms = abs(int(line3[0]))

        V1 = FI.readline()
        V2 = FI.readline()
        V3 = FI.readline()

        for _ in range(natoms):
            s = FI.readline().strip().split()
            elN, xyz = s[0], map(lambda x: str(float(x)*Bohr), s[2:])
            self.geom.coord.append('%s    %s  %s  %s\n' % tuple([elN]+xyz))

        FI.close()
        log.debug('%s parsed successfully' % (self.file))
        return


    def webData(self):
        """
        Makes HTML row.
        return: b1,b2
        """

        we = self.settings.Engine3D()
        wp = self.geom.write(fname='.xyz')
        b1 = we.JMolApplet(webpath = wp)

        iso_on = self.s_script
        iso_off = 'isosurface off'
        b2 = we.JMolButton(iso_on,label='Isosurface On') + we.JMolButton(iso_off,label='Off')

        log.debug('webData generated successfully')
        return b1, b2


    def make_JVXL(self):
        """
        * [V] It is to be called by parser
        * [V] At the moment of call, Jmol script line has to be known
        * make_JVXL should call external Jmol
        * make_JVXL will return updated Jmol script command
        """
        J = JVXL()
        J.file = re.sub('cube$','jvxl',self.file)
        J.wp = re.sub('cube$','jvxl',self.wpcube)
        #J.file = self.settings.realPath('.jvxl')
        #J.wp =  self.settings.webPath('.jvxl')

        s = "%s; write jvxl %s" % (self.s_script,J.file)
        RunJmol(self.settings.JmolAbsPath,s)
        we = self.settings.Engine3D()
        J.s_script = we.JMol_JVXL(webpath = J.wp,name=self.name)
        self.s_script = J.s_script
        return J


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
