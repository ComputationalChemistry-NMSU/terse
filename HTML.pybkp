import Tools.web as web
from Top import Top
import logging
log = logging.getLogger(__name__)

class HTML(Top):
    def __init__(self):
        self.s = ''
        self.tableBody = ''


    def __str__(self):
        return self.s


    def readTemplate(self,fname=''):
        if not fname:
            fname = '%sTemplates/terse-%s.html' % (self.settings.selfPath,self.settings.Engine3D.__name__)
        self.s = open(fname).read()


    def addTableRow(self,*args):
        row = ''
        for a in args:
            row += web.tag(a,'td')+'\n'
        self.tableBody += web.tag(row,'tr')


    def write(self, file=''):
        if not file:
            file = self.settings.OutputFolder + '/' + self.settings.tersehtml
        try:
            f = open(file,'w')
        except IOError:
            log.critical('Cannot open %s for writing' % (file))
            return
        f.write(self.s)
        f.close()
        log.debug('Web page %s was created' % (file))


    def finalize(self):
        d = {
                'JSMolPath' : self.settings.JSMolLocation,
                'timestamp' : self.settings.timestamp,
                'JMolPath'  : self.settings.JmolPath,
                'TableBody' : self.tableBody,
                'JMolWinX'  : self.settings.JmolWinX,
                'JMolWinY'  : self.settings.JmolWinY,
            }
        self.s = self.s % d




if __name__ == "__main__":
    h = HTML()
    from Settings import Settings
    h.settings = Settings()
    tr = web.tag('abcd','tr')

    # This code is outdated!
    h.makeHeader()
    h.makeLine('abc','def')
    h.makeTail()
    print h
