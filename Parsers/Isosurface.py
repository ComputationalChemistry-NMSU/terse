if __name__ == "__main__":
    import sys,os
    append_path = os.path.abspath(sys.argv[0])[:-22]
    print "Append to PYTHONPATH: %s" % (append_path)
    sys.path.append(append_path)

import time,logging
import subprocess
from Top import Top
from Tools.IO import is_readable
from Parsers.FchkGaussian import FchkGaussian
from Parsers.ChkGaussian import ChkGaussian
from Parsers.Cube import Cube
import os
log = logging.getLogger(__name__)





class Isosurface(Top):
    """
    Shows isosurfaces from .chk/.fchk files
    """

    def __init__(self):
        self.fchk = None
        self.SpecificProp = False

    def parse(self):
        if 'c' in self.file:
            if not is_readable(self.file['c']):
                return
            chk = ChkGaussian()
            chk.file = self.file['c']
            self.surface = chk.formchk()

        elif 'f' in self.file:
            if not is_readable(self.file['f']):
                return
            self.surface = FchkGaussian()
            self.surface.file = self.file['f']

        elif 'cb' in self.file:
            if not is_readable(self.file['cb']):
                return
            self.surface = Cube()
            self.surface.file = self.file['cb']

        else:
            log.error('No Gaussian Checkpoint file name provided')

        self.surface.isotype = self.file['type']
        if 'iv' in self.file:
            self.surface.isovalue = self.file['iv']
        self.surface.parse()


    def postprocess(self):
        self.surface.postprocess()


    def webData(self):
        b1, b2 = self.surface.webData()
        return b1,b2

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
