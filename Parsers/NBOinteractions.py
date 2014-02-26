if __name__ == "__main__":
    import sys,os
    selfname = sys.argv[0]
    full_path = os.path.abspath(selfname)[:]
    last_slash = full_path.rfind('/')
    dirpath = full_path[:last_slash] + '/..'
    print "Append to PYTHONPATH: %s" % (dirpath)
    sys.path.append(dirpath)

import time,re,logging
import math
from Tools import web
from Tools.IO import is_readable
from Tools.BetterFile import BetterFile
from Parsers.Gaussian import Gaussian
from Parsers.ChkGaussian import ChkGaussian
from Top import Top
import re
log = logging.getLogger(__name__)





class NBOinteractions(Top):
    """
    Shows orbital interactions. Two files are needed, Gaussian .log (with NBO output) and .chk (with NBO isosurfaces)
    """
    def __init__(self):
        self.fileL = ''
        self.fileC = ''
        self.L = Gaussian()
        self.C = ChkGaussian()

    def LookUpChkInLog(self):
        FL = BetterFile(self.fileL)
        if not FL.skip_until(['^ #','(?i)%chk'],regexp=True):
            log.debug('Checkpoint file name not found in %s' % (self.fileL))
            return ''
        log.debug('Checkpoint file name found in %s' % (self.fileL))
        slash = self.fileL.rfind('/') + 1
        path = self.fileL[:slash]
        return path + FL.s.strip().split('=')[1]

    def LookUpByBasename(self):
        lastDot = self.fileL.rfind('.')
        return self.fileL[:lastDot] + '.chk'


    def parse(self):
        #self.file = self.file[0]

        if not 'l' in self.file:
            log.error('NBOinteraction requires Gaussian .log file as input')
            return
        self.fileL = self.file['l']
        if not is_readable(self.fileL):
            return
        self.L.file = self.fileL

        if 'c' in self.file:
            self.fileC = self.file['c']
        else:
            log.debug('Gaussian checkpoint file name is not provided in the input; trying to guess...')
            self.fileC = self.LookUpChkInLog()
            if self.fileC:
                log.debug('Checkpoint file found: %s' % (self.fileC))
            else:
                self.fileC = self.LookUpByBasename()
        if not is_readable(self.fileC):
            return
        self.C.file = self.fileC
        self.L.parse()
        self.C.parse()


    def postprocess(self):
        self.L.postprocess()
        self.C.postprocess()
        self.nbo = None
        for Lstep in self.L.steps:
            for g in Lstep.geoms:
                if hasattr(g,'nbo_analysis'):
                    self.nbo = g.nbo_analysis


    def webData(self):
        """
        Returns 2 strings with HTML code
        """
        # Show weird bond angles topology

        we = self.settings.Engine3D()

        Lb1, Lb2 = self.L.webData()
        Cb1, Cb2 = self.C.webData()

        b1 = Lb1

        b2  = web.tag('Gaussian Log File','strong')+web.brn + Lb2
        b2 += web.tag('Gaussian Chk File','strong')+web.brn + Cb2

        #---
        def set_webData(nbo_result):
            s = ''
            any_shown = False
            script_off = 'isosurface off; '
            if 't' in self.file:
                threshold = float(self.file['t'])
            else:
                threshold = float(self.settings.inbo_threshold)

            cubes_done = {}
            for sopta in nbo_result.sopta:
                if float(sopta.e2) > threshold:
                    any_shown = True
                    s += '%s -> %s: %s kcal/mol' % (sopta.donor.sorb, sopta.acceptor.sorb, sopta.e2)
                    i_donor = str(sopta.donor.chk_index)
                    if i_donor in cubes_done:
                        c_donor = cubes_done[i_donor]
                    else:
                        c_donor = self.C.fchk.makeCube('MO='+i_donor, name='mo'+i_donor)

                    i_acceptor = str(sopta.acceptor.chk_index)
                    if i_acceptor in cubes_done:
                        c_acceptor = cubes_done[i_acceptor]
                    else:
                        c_acceptor = self.C.fchk.makeCube('MO='+i_acceptor, name='mo'+i_acceptor,colors='phase green yellow')

                    script = "%s ; %s ; %s" % (script_off, c_donor.s_script, c_acceptor.s_script)
                    #script += we.JMolIsosurface(webpath = c_donor.wpcube,  surftype='MO',name='mo'+i_donor)
                    #script += "; "
                    #script += we.JMolIsosurface(webpath = c_acceptor.wpcube,  surftype='MO',name='mo'+i_acceptor,colors='phase green yellow')
                    s += we.JMolButton(action=script,label='Show')
                    s += web.brn
            if any_shown:
                s += we.JMolButton(action=script_off,label='Off')
            return s
        #---
        if self.nbo.options:
            b2 += web.tag('Options:','strong')+web.brn
            b2 += self.nbo.options + web.brn
        if self.nbo.comments:
            b2 += self.nbo.comments + web.brn
        if self.nbo.OpenShell:
            b2 += web.tag('Alpha spin NBO interactions','strong') + web.brn
            b2 += set_webData(self.nbo.setA)
            b2 += web.tag('Beta spin NBO interactions','strong') + web.brn
            b2 += set_webData(self.nbo.setB)
        else:
            b2 += web.tag('NBO interactions','strong') + web.brn
            b2 += set_webData(self.nbo.setAB)

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

    f = NBOinteractions()
    f.file = sys.argv[1:]
    f.parse()
