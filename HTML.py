import Tools.web as web
from Top import Top
import logging
log = logging.getLogger(__name__)

class HTML(Top):
    def __init__(self):
        self.s = ''
        self.pageBody = ''


    def __str__(self):
        return self.s


    def readTemplate(self,fname=''):
        if not fname:
            fname = '%sTemplates/terse-%s.html' % (self.settings.selfPath,self.settings.Engine3D.__name__)
        self.s = open(fname).read()

    def addLeftDiv(self,*args):
        left_panel = ''
        for a in args:
            left_panel += web.tag(a,'div',"id='left_panel'")+'\n'
        return left_panel

    def addRightDiv(self,*args):
        right_panel = ''
        for a in args:
            right_panel += web.tag(a,'div',"id='right_panel'")+'\n'
        return right_panel

    def addDivRowWrapper(self,*args):
        row = ''
        for a in args:
            row += a
        self.pageBody += web.tag(row,'div')


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
                'pageBody'  : self.pageBody,
                'JMolWinX'  : self.settings.JMolWinX,
                'JMolWinY'  : self.settings.JMolWinY,
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
