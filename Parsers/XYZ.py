if __name__ == "__main__":
    import sys
    sys.path.append('..')

import Tools.web as web
import Geometry
from Top import Top
import ChemicalInfo
import logging
log = logging.getLogger(__name__)


class XYZ(Top):
    def __init__(self):
        self.vector = []
        self.noAtoms = 0
        self.geoms = Geometry.ListGeoms()
        self.scan = None
        self.wp = ''


    def parse(self):
        """
        Parses XYZ file both in standard and short (without header) formats.
        Can read parameters from comment lines in format '%s= %s'.
        If .XYZ file contains several geoemtries, a graph can be plot
        (for now, IRC mode turns on if 'e' and 'x' parameters are given
        for each geometry; if other parameter instead of 'x' is given,
        Scan mode is activated)
        """

        # Open file
        try:
            FI = open(self.file)
            log.debug('%s was opened for reading' %(self.file))
        except:
            log.error('Cannot open %s for reading' %(self.file))
            return '',''
        #
        # Read file
        #
        geom = Geometry.Geom()
        is_FirstLine = True
        for s in FI:
            splitted = s.strip().split()
            if len(splitted) > 3:
                if is_FirstLine: # Short XYZ
                    log.debug('Short XYZ format (without headers) recognized')
                    is_FirstLine = False
                # Read Coords
                splitted[0] = ChemicalInfo._to_elN(splitted[0])
                geom.coord.append('%s    %s  %s  %s\n' % tuple(splitted[:4]))
                # +Vectors
                if len(splitted)==7:
                    log.debug('Displacement vectors found')
                    self.vector.append('%s  %s  %s\n' % tuple(splitted[4:]))
                #
            elif len(splitted)==1:
                if is_FirstLine: # Standard XYZ
                    is_FirstLine = False
                    log.debug('Standard XYZ format recognized')
                else:
                    self.geoms.append(geom)
                # New Record
                geom = Geometry.Geom()
                try:
                    geom.header_natoms = int(splitted[0])
                except:
                    log.warning('Cannot read number of atoms from the header')
                try:
                    comment = FI.next().strip()
                except:
                    log.warning('Unexpected EOF while reading comment line')
                geom.parseComment(comment)
        self.geoms.append(geom)
        FI.close()


    def postprocess(self):
        """
        Some operations on parsed data
        """
        log.debug('%i geometries found' % (len(self.geoms)))

        if self.vector:
            log.debug('Vectors found')

        #self.geoms.consistencyCheck()
        # import conversion units
        if self.geoms[-1].to_kcalmol:
            self.to_kcalmol = self.geoms[-1].to_kcalmol
        else:
            self.to_kcalmol = 1.

        # Do we have extended data?
        if 'e' in self.geoms.props:
            if 'x' in self.geoms.props:
                self.scan = Geometry.IRC(other=self.geoms)
                log.debug('IRC plot will be shown')
            else:
                self.scan = Geometry.Scan(other=self.geoms)
                log.debug('Scan plot will be shown')

        log.debug('XYZ file parsed successfully')


    def webData(self):
        """
        Makes HTML row.
        If some parameteres were read from comment sections of .xyz files,
        graph is plotted
        return: b1,b2
        """

        we = self.settings.Engine3D()

        JmolScript = ''
        b2 = web.tag('Comments:','strong') + web.brn + self.geoms.comment
        if self.scan:
            b2 += self.scan.webData()
            JmolScript += we.measureGau(self.scan.props)
            self.wp = self.scan.write(fname='.xyz',vectors=self.vector)
        else:
            self.wp = self.geoms.write(fname='.xyz',vectors=self.vector)
        b1 = we.JMolApplet(webpath = self.wp, ExtraScript = JmolScript) + web.brn

        if len(self.geoms.geoms)>1:
            b1 += we.MultipleGeoms()
        elif self.vector:
            b1 += we.JMolCheckBox('vibration on','vibration off', 'Vibration')

        log.debug('webData generated successfully')
        return b1, b2


    def write(self, fname, geoms=None, vectors=None):
        """
        To keep things where they belong to,
        we store XYZ writer here. However, the only places where
        it is called from is ListGeoms and Geom write functions,
        because we can apply it only to geometries
        """
        if not geoms:
            log.warning('File %s: No coordinates to write!' % (fname))
            return

        file = self.settings.realPath(fname)
        try:
            f = open(file,'w')
        except IOError:
            log.critical('Cannot open file "%s" for writing' % (file))
            return

        if vectors:
            if len(vectors) != len(geoms[0]):
                log.warning('writeXYZ: coords and vectors have different lengths')
                vectors = None
            if len(geoms) > 1:
                log.warning('writeXYZ: Several geometries found; turning Vibrations off')
                vectors = None

        for i in range(len(geoms)):
            geom = geoms[i]
            comment = geom.propsToString(ShowComment = True)
            f.write('%s\n%s\n' % (len(geom.coord), comment))
            for j in range(len(geom.coord)):
                if vectors:
                    f.write(geom.coord[j].strip()+'     '+vectors[j].strip()+'\n')
                else:
                    f.write(geom.coord[j].strip()+'\n')
        f.close()
        log.debug('Coordinates were written to file ' + file)
        return self.settings.webPath(fname)

#
#
#
if __name__ == "__main__":
    DebugLevel = logging.DEBUG
    logging.basicConfig(level=DebugLevel)

    from Settings import Settings
    Top.settings = Settings(FromConfigFile = True)

    from HTML import HTML
    WebPage = HTML()
    WebPage.makeHeader()

    f = XYZ()
    f.file = sys.argv[1]
    #import profile
    #profile.run('f.parse()')
    f.parse()
    print f.geoms
    b1, b2 = f.webData()

    WebPage.makeLine(b1,b2)
    WebPage.makeTail()
    WebPage.write()
