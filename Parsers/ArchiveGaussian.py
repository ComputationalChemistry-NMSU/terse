if __name__ == "__main__":
    import sys,os
    append_path = os.path.abspath(sys.argv[0])[:-20]
    print "Append to PYTHONPATH: %s" % (append_path)
    sys.path.append(append_path)

import re
import math
import Tools.web as web
from Tools.BetterFile import BetterFile
import ChemicalInfo
from Geometry import Scan,IRC,Geom,ListGeoms
from ElStr import ElectronicStructure
from Containers import AtomicProps,Topology
from Parsers.NBO import NBO

import logging
log = logging.getLogger(__name__)


#TODO read solvent from the route line
#TODO Read thermochemistry appendix

class ArchiveGaussian(ElectronicStructure):
    """
    Gaussian 09 parser
    Analyzes a multiple-step calculation
    """

    def __init__(self):
        """
        Declares steps (type List)
        """
        self.steps = []


    def parse(self):
        """
        Parses Gaussian log file, step by step
        """

        FI = BetterFile(self.file)
        FI.skip(2)

        while True:
            step = ArchiveGauStep(FI)
            step.parse()
            step.postprocess()
            if step.blanc:
                break
            self.steps.append(step)

        FI.close()
        log.debug('%s parsed successfully' % (self.file))
        return


    def webData(self):
        """
        Returns 2 strings with HTML code
        """

        we = self.settings.Engine3D()

        b1,b2,bb1,bb2,i = '','','','',1
        b1s = []
        for step in self.steps:
            self.settings.subcounter += 1
            b1, b2 = step.webData(StartApplet=False)
            labeltext = '%s: %s' %(step.JobType,step.lot)
            b1s.append([b1,labeltext.upper()])
            bb2 += b2
            i += 1

        if b1s:
            bb1 = we.JMolApplet(ExtraScript = b1s[-1][0])
            if len(b1s)>1:
                bb1 += web.brn*2
                for b1 in b1s:
                    bb1 += we.JMolButton(*b1)

        log.debug('webData generated successfully')
        return bb1, bb2





class ArchiveGauStep(ElectronicStructure):
    """
    Works with a single calculation step
    """


    def parse(self):
        """
        Actual parsing happens here
        """

        self.all_coords = {}

        """
        Occur only in the first entrance, so we just safely skip
        these two lines right after opening the file
        s01                          = self.FI.nstrip()
        s02                          = self.FI.nstrip()
        """
        try:
            s03                          = self.FI.nstrip()
        except:
            self.blanc = True
            return
        s04_compnode                 = self.FI.nstrip()
        s05_type                     = self.FI.nstrip()
        s06_lot                      = self.FI.nstrip()
        s07_basis                    = self.FI.nstrip()
        s08_stochiometry_charge_mult = self.FI.nstrip()
        s09_user                     = self.FI.nstrip()
        s10_date                     = self.FI.nstrip()
        s11                          = self.FI.nstrip()
        s12                          = self.FI.nstrip()
        s13_route                    = self.FI.nstrip()
        s14                          = self.FI.nstrip()
        s15_comment                  = self.FI.nstrip()
        s16                          = self.FI.nstrip()
        s17_charge_mult              = self.FI.nstrip()
        s18_geom                     = self.FI.getBlock(StartOffset=1)
        s_ag_variables               = self.FI.getBlock(StartOffset=1) # after geometry

        self.OK = True
        # Read in values in the header part
        self.JobType = s05_type.lower()
        self.lot = s06_lot
        self.basis = s07_basis
        self.extra = s13_route
        self.comments = s15_comment
        self.charge, self.mult = s17_charge_mult.split(',')

        if 'scrf' in s13_route.lower():
            solvent = re.search('scrf.*solvent\s*=\s*(\w+)',s13_route.lower())
            if solvent:
                self.solvent = solvent.group(1)
        # Read in geom
        geom = Geom()
        atnames = []
        for s in s18_geom:
            xyz = s.strip().split(',')
            try:
                atn, x,y,z = xyz[0], xyz[-3],xyz[-2],xyz[-1]
            except:
                log.warning('Error reading coordinates:\n%s' % (s))
                break
            atnames.append(atn)
            geom.coord.append('%s %s %s %s' % (atn,x,y,z))
        pc = AtomicProps(attr='atnames',data=atnames)
        geom.addAtProp(pc,visible=False)
        self.geoms.geoms.append(geom)

        # Read in variables
        vrs = {}
        for s in s_ag_variables:
            k,v = s.split('=')
            vrs[k] = v

        if 'S2A' in vrs:
            self.s2 = '%s / %s' % (vrs['S2'],vrs['S2A'])

        if 'HF' in vrs:
            self.scf_e = float(vrs['HF'])

        if 'NImag' in vrs:
            self.nimag = float(vrs['NImag'])
            if self.nimag > 0:
                self.extra += 'Imaginary freqs found!'

        try:
            self.FI.skip_until('@1')
        except:
            pass
        return




    def postprocess(self):
        #
        # ======================================= Postprocessing  ======================================================
        #
        log.debug('Gaussian step (%s) parsed successfully' %(self.JobType))
        return



#
#
#
#
#
if __name__ == "__main__":

    DebugLevel = logging.DEBUG
    logging.basicConfig(level=DebugLevel)

    from Settings import Settings
    from Top import Top
    Top.settings = Settings(FromConfigFile = True)

    from HTML import HTML
    WebPage = HTML()
    WebPage.makeHeader()

    f = Gaussian()
    f.file = sys.argv[1]
    #import profile
    #profile.run('f.parse()')
    f.parse()
    f.postprocess()
    print f.steps[0]
    b1, b2 = f.webData()

    WebPage.makeLine(b1,b2)
    WebPage.makeTail()
    WebPage.write()
