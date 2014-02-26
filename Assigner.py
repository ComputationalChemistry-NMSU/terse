import os
import logging
from Top import Top
from Parsers.NBOinteractions import NBOinteractions
from Parsers.ChkGaussian import ChkGaussian
from Parsers.FchkGaussian import FchkGaussian
from Parsers.Isosurface import Isosurface
from Parsers.JVXL import JVXL
log = logging.getLogger(__name__)

class ParserAssigner(Top):
    def __init__(self):
        self.exts = {}
        # Register extensions
        for attr,value in self.settings.__dict__.iteritems():
            if '_extension' in attr:
                progname = attr.strip().split('_extension')[0]
                values = value.replace(' ','').split(',')
                for v in values:
                    self.exts[v] = progname
        log.debug('Registered extensions: %s' % (self.exts))


    def typeByCommandLine(self, frecord):
        """
        Assign a class to frecord
        """
        rectype, params = frecord[0], frecord[1:]
        if rectype == 'file':
            return


        type2class = {
                'inbo'     : NBOinteractions,
                'iso'      : Isosurface,
                'jvxl'     : JVXL,
                'top'      : Top
                }

        return type2class[rectype]()



    def typeByExt(self, frecord):
        """
        Assign a class to frecord
        """
        rectype, params = frecord[0], frecord[1:]
        if rectype != 'file':
            return

        top = Top()
        file = params[0]
        base, ext = os.path.splitext(file)
        ext = ext[1:]
        try:
            ParsingClass = self.exts[ext]
            log.info( '%s parser is selected for %s' %(ParsingClass,file))
        except KeyError:
            log.error("Extension '%s' is not registered" % (ext))
            return top

        ModName = 'Parsers.'+ParsingClass
        GenericParser = __import__(ModName)
        module = getattr(GenericParser,ParsingClass)
        try:
            ModName = 'Parsers.'+ParsingClass
            GenericParser = __import__(ModName)
            module = getattr(GenericParser,ParsingClass)
        except:
            log.error("Module '%s' cannot be loaded" % (ModName))
            return top

        try:
            cl = eval('module.'+ParsingClass)()
            log.debug('Assigned parser was successfully loaded')
            return cl
        except NameError:
            log.error("Parser '%s' cannot be loaded" % (ParsingClass))
            return top


    def typeByContent(self,frecord):
        #TODO To be implemented
        rectype, params = frecord[0], frecord[1:]
        top = Top()
        return top

