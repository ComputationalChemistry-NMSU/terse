from Top import Top
import Tools.web as web
import logging

log = logging.getLogger(__name__)


class JSMol(Top):

    def JSMolStyle(self, s):
        s2 = "Jmol.script(jmolApplet%(counter)s, \"%(script)s\" );" % {
                'counter' : self.settings.counter,
                'script' : s.replace('"','\\"').replace("'","\\'")#s.replace('"',' &quot ')
                }
        return s2

    def JSMolScript(self, s, intag=''):
        s2 = self.JSMolStyle(s)
        return web.tag(s2,'SCRIPT',intag=intag)


    def JMolApplet(self, webpath='', ExtraScript=''):
        s = "jmolApplet%s = Jmol.getApplet(\"jmolApplet%s\", Info)" % ((self.settings.counter,)*2)
        script = self.JMolLoad(webpath=webpath,ExtraScript=ExtraScript)
        s += ';\n' + self.JSMolStyle(script)
        return web.tag(s,'SCRIPT')


    def JMolLoad(self, webpath='', ExtraScript=''):
        sl = ''
        if webpath:
            sl = 'load %s;%s' % (webpath, self.settings.JavaOptions)
        if ExtraScript:
            sl += ExtraScript
        return sl


    def JMolIsosurface(self, webpath='',isovalue = '', surftype = '', webpath_other='',name='',colors='',use_quotes=False):
        isovals = {
              'potential' : '0.001',
              'spin'      : '0.001',
              'mo'        : '0.03',
              'amo'       : '0.03',
              'bmo'       : '0.03'
                }
        surftypes = {
                'potential' : 'isosurface %s %s %s color absolute -0.03 0.03 map %s',
                'spin'      : 'isosurface %s sign %s %s %s',
                'mo'        : 'isosurface %s phase %s %s %s',
                'amo'       : 'isosurface %s phase %s %s %s',
                'bmo'       : 'isosurface %s phase %s %s %s'
                }
        coltypes = {
                'mo'         : 'phase %s %s opaque' % (self.settings.color_mo_plus, self.settings.color_mo_minus),
                'amo'        : 'phase %s %s opaque' % (self.settings.color_mo_plus, self.settings.color_mo_minus),
                'bmo'        : 'phase %s %s opaque' % (self.settings.color_mo_plus, self.settings.color_mo_minus),
                'spin'       : 'red blue translucent'
                }

        st_lower = surftype.lower().split('=')[0]
        if st_lower in surftypes:
            st = surftypes[st_lower]
        else:
            st = 'isosurface %s %s %s %s'

        if not isovalue:
            if st_lower in isovals:
                isovalue = isovals[st_lower]
            else:
                isovalue = '0.03'

        color=colors
        if (st_lower in coltypes) and (not color):
            color = coltypes[st_lower]
        if not color:
            color = 'translucent'

        if use_quotes:
            webpath = '"%s"' % (webpath)
            if webpath_other:
                webpath_other = '"%s"' % (webpath_other)

        log.debug('Plotting isosurface; surftype: %s' % (st_lower))
        st2 = st % (name,isovalue,webpath, webpath_other) + '; color isosurface %s' % (color)
        return st2


    def JMol_JVXL(self, webpath='',name='',use_quotes=False):

        if use_quotes:
            webpath = '"%s"' % (webpath)

        st2 = 'isosurface %s %s' % (name,webpath)
        return st2


    def JMolCommandInput(self):
        s = 'jmolCommandInput("Execute")'
        return self.JSMolScript(s)


    def JMolText(self,label,position='top left',color='green',script=True):
        s = "set echo %s; color echo %s; echo %s;" % (position,color,label)
        if script:
            s = self.JSMolScript(s)
        return s


    def JMolCheckBox(self, on, off, label=''):
        s = 'jmolCheckbox("%s", "%s", "%s")' % (on, off, label)
        return self.JSMolScript(s)


    def JMolButton(self, action, label):
        #s = 'jmolButton("%s","%s")' % (action, label)
        s = '<button type="button" onclick="javascript:Jmol.script(jmolApplet%(count)s, \'%(action)s\')">%(label)s</button>' % {
                'count'  : self.settings.counter,
                'action' : action.replace('"','\\"').replace("'","\\'"),#s.replace('"',' &quot '),
                'label'  : label,
                }
        return s


    def JMolRadioGroup(self, options):
        s = ''
        for opt in options:
            s2 = ''
            for o in opt:
                s2 += '"%s", ' % (o)
            s += '[%s],' % (s2[:-2])
        s = 'jmolRadioGroup([%s])' % (s[:-1])
        return self.JSMolScript(s)


    def JMolMenu(self, options,script=True):
        s = ''
        for opt in options:
            s2 = ''
            for o in opt: s2 += '"%s", ' % (o)
            s += '[%s],' % (s2[:-2])
        s = 'jmolMenu([%s])' % (s[:-1])
        if script:
            s = self.JSMolScript(s)
        return s


    def MultipleGeoms(self):
        ButtonFirst = self.JMolButton('frame 1','<<')
        ButtonPrev =  self.JMolButton('anim direction +1 ; frame prev','<')
        ButtonNext =  self.JMolButton('anim direction +1 ; frame next','>')
        ButtonLast =  self.JMolButton('frame last','>>')
        ButtonPlayOnce =  self.JMolButton('anim mode once; frame 1; anim direction +1 ; anim on','Play once')
        ButtonPlayBack =  self.JMolButton('anim mode once; frame 1; anim direction -1 ; anim on','Play back')
        ButtonStop =  self.JMolButton('anim off','Stop')

        s  = ButtonFirst + ButtonPrev + ButtonNext + ButtonLast
        s += ButtonPlayOnce + ButtonPlayBack + ButtonStop

        """
        opts = []
        for a in (1,5,10,25,50):
            opts.append(['set animationFPS %s' % (a), a])
        opts[2].append('checked')

        s += self.JMolMenu(opts,script=False)
        """
        return s
        return self.JSMolScript(s)


    def Vibration(self):
        #s = 'jmolCheckbox("vibration on", "vibration off", "Vibration");'
        s  = self.JMolButton('vibration on','Vibration On')
        s += self.JMolButton('vibration off','Off')
        return s
        return self.JSMolScript(s)


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
