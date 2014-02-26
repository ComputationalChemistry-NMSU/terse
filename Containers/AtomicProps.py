if __name__ == "__main__":
    import sys
    sys.path.append('..')

import logging
from Top import Top
log = logging.getLogger(__name__)



class AtomicProps(Top):
    """
    This is a container for atomic properties.
    Expected functionality:
        1. Provide data structure to store atomic properties,
        2. Visualize properties in Jmol using labels and color gradients
    """

    def __init__(self,attr='partialCharge',data=None):
        self.attrname = attr
        if data == None:
            self.data = []
        else:
            setattr(self,attr,data)
            self.data = data


    def __str__(self,precision=6):
        """
        Represents list as string with space-separated values
        rype: string
        """

        if len(self.data) == 0:
            return ''
        a0 = self.data[0]
        type2format = {
                int   : '%i ',
                float : '%.' + str(precision) + 'f ',
                str   : '%s '
                }
        template = (type2format[a0.__class__])*len(self.data)
        s = template % tuple(self.data)
        return s.rstrip()


    def webData(self,precision=2):
        if '_H' in self.attrname:
            H_1 = "label off ; select not Hydrogen ;"
            H_2 = "; select all"
        else:
            H_1 = ""
            H_2 = ""
        script_on = "x='%(a)s'; DATA '%(p)s @x'; %(H_1)s label %%.%(precision)s[%(p)s]; color atoms %(p)s 'rwb' absolute -1.0 1.0 %(H_2)s" % {
                'a'         : str(self),
                'p'         : 'property_'+self.attrname,
                'precision' : str(precision),
                'H_1' : H_1,
                'H_2' : H_2
                }
        script_off = "label off ; color atoms cpk"
        we = self.settings.Engine3D()
        return we.JMolButton(script_on,self.attrname);


if __name__ == '__main__':
    from Settings import Settings
    settings = Settings(FromConfigFile = True)
    ap = AtomicProps(attr='partialCharge')
    ap.settigns = settings
    ap.data = [-0.2,-0.2,-0.2,0.3,0.3,.5,-.5]
    #print ap
    print ap.webData()
