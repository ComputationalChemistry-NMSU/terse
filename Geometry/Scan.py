from Geometry import ListGeoms

import logging
log = logging.getLogger(__name__)

class Scan(ListGeoms):

    def webData(self,SortGeom = False):
        self.ces = self.toBaseLine(EnFactor=float(self.settings.EnergyFactor))
        s = ''
        for prop in self.props:
            if prop != 'e':
                x = getattr(self, prop)
            else:
                x = []
            s = self.plot(x=x, xlabel=prop, y=[self.ces])
            s += self.extrema(title='Scan min/max points :',yg=self.ces,frame_names=x,frame_prefix=prop+'=')
        return s
