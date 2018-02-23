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
import os
log = logging.getLogger(__name__)





class ChkGaussian(Top):
    """
    Shows 3D-properties from the .chk file
    """

    def __init__(self):
        self.fchk = None
        self.SpecificProp = False


    def formchk(self,fname=''):
        fchk = FchkGaussian()
        if fname:
            chk_file = fname
        else:
            chk_file = self.file

        fchk.file = self.settings.realPath('.fchk')

        command = (self.settings.formchk, chk_file, fchk.file)
        output = subprocess.call(command)

        if not os.path.exists(fchk.file):
            log.warning('Conversion to .fchk file failed')
            return None

        log.debug('Chk file succefully converted to .fchk file')
        return fchk


    def parse(self):
        self.fchk = self.formchk()
        self.fchk.parse()


    def postprocess(self):
        self.fchk.postprocess()


    def webData(self):
        b1, b2 = self.fchk.webData()
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

    f = ChkGaussian()
    f.file = sys.argv[1]
    f.parse()
    print f
