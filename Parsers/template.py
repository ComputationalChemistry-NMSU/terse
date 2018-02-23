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
log = logging.getLogger(__name__)





class Parser(Top):
    """
    Shows 3D-properties from the .chk file
    """


    def parse(self):
		pass

    def postprocess(self):
		pass


    def webData(self):
		pass
        """
        Returns 2 strings with HTML code
        """

        we = self.settings.Engine3D()

        b1, b2 = '', ''
		# ...
        log.debug('webData generated successfully')
        return bb1, bb2
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
