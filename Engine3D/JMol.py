from Top import Top
import Tools.web as web
import logging

log = logging.getLogger(__name__)

class JMol(Top):

    def JMolApplet(self, webpath='', ExtraScript=''):
        script = self.JMolLoad(webpath=webpath,ExtraScript=ExtraScript)
        s = 'jmolApplet([%s,%s],"%s")' % (self.settings.JmolWinX, self.settings.JmolWinY, script)
        return web.tag(s,'SCRIPT')


    def JMolLoad(self, webpath='', ExtraScript=''):
        sl = ''
        if webpath:
            sl = 'load %s;%s' % (webpath, self.settings.JavaOptions)
        if ExtraScript:
            sl += '; ' + ExtraScript
        return sl


    def JMolIsosurface(self, webpath='',isovalue = 0.03, surftype = None, webpath_other='',name='',colors=''):
        if surftype:
            surftypes = {
                    'Potential' : 'isosurface %s 0.001 %s color absolute -0.03 0.03 map %s',
                    'Spin'      : 'isosurface %s sign 0.001 %s %s',
                    'MO'        : 'isosurface %s phase 0.03 %s %s',
                    'AMO'       : 'isosurface %s phase 0.03 %s %s',
                    'BMO'       : 'isosurface %s phase 0.03 %s %s'
                    }
            st = surftypes[surftype]
        else:
            st = 'isosurface %%s %s %%s %%s' % (isovalue)
        st2 = st % (name,webpath, webpath_other) + '; color isosurface %s translucent' % (colors)
        return st2


    def JMolCommandInput(self):
        s = 'jmolCommandInput("Execute")'
        return web.tag(s,'SCRIPT')



    def JMolText(self,label,position='top left',color='green',script=True):
        s = "set echo %s; color echo %s; echo %s;" % (position,color,label)
        if script:
            s = web.tag(s,'SCRIPT')
        return s

    def JMolCheckBox(self, on, off, label=''):
        s = 'jmolCheckbox("%s", "%s", "%s")' % (on, off, label)
        return web.tag(s,'SCRIPT')

    def JMolButton(self, action, label):
        s = 'jmolButton("%s","%s")' % (action, label)
        return web.tag(s,'SCRIPT')


    def JMolRadioGroup(self, options):
        s = ''
        for opt in options:
            s2 = ''
            for o in opt:
                s2 += '"%s", ' % (o)
            s += '[%s],' % (s2[:-2])
        s = 'jmolRadioGroup([%s])' % (s[:-1])
        return web.tag(s,'SCRIPT')


    def JMolMenu(self, options,script=True):
        s = ''
        for opt in options:
            s2 = ''
            for o in opt: s2 += '"%s", ' % (o)
            s += '[%s],' % (s2[:-2])
        s = 'jmolMenu([%s])' % (s[:-1])
        if script:
            s = web.tag(s,'SCRIPT')
        return s


    def MultipleGeoms(self):
        s = """jmolButton("frame 1","<<");
        jmolButton("anim direction +1 ; frame prev","<");
        jmolButton("anim direction +1 ; frame next",">");
        jmolButton("anim direction +1 ;frame last",">>");
        jmolButton("anim mode once; frame 1; anim direction +1 ; anim on", "Play once");
        jmolButton("anim mode once; frame last ; anim direction -1 ; anim on", "Play back");
        jmolButton("anim off", "Stop");
        """

        opts = []
        for a in (1,5,10,25,50):
            opts.append(['set animationFPS %s' % (a), a])
        opts[2].append('checked')

        s += self.JMolMenu(opts,script=False)
        return web.tag(s,'SCRIPT')


    def Vibration(self):
        s = 'jmolCheckbox("vibration on", "vibration off", "Vibration");'
        return web.tag(s,'SCRIPT')


    def measureGau(self,ss):
        toJmol = ''
        for s in ss:
            left, right = s.find('('), s.find(')')
            if left and right and (right > left):
                toJmol += 'measure %s; ' %(s[left+1:right].replace(',',' '))
        return toJmol

if __name__ == "__main__":
    import sys
    sys.path.append('..')
    #from Settings import Settings
