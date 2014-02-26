from Geometry import ListGeoms
import Tools.web as web

import logging
log = logging.getLogger(__name__)

class IRC(ListGeoms):

    def __init__(self,other=None):
        #IRC specific lines
        self.direction = 1
        self.both = False
        ListGeoms.__init__(self,other)

    def __nonzero__(self):
        if self.x and self.e:
            return True
        else:
            return False

    def webData(self,SortGeom = False):
        b_gradFromE = True
        # set energies to a baseline and normalize gradients
        self.ces = self.toBaseLine()
        #IRC Specific
        if b_gradFromE:
            self.grad = [0,]
            for i in range(1,len(self.x)-1):
                de = self.ces[i+1]-self.ces[i-1]
                dx = float(self.x[i+1])-float(self.x[i-1])
                self.grad.append(abs(de/dx))
            self.grad.append(0)
            is_ircgrad = self.settings.ircgrad and hasattr(self,'grad') and self.grad
        else:
            is_ircgrad = self.settings.ircgrad

        if is_ircgrad:
            if self.ces:
                self.cgrad = self.normalizeGradients(mx=max(self.ces))
            else:
                self.cgrad = []

        # Prepare comments
        """
        self.comments = self.applyComments()
        if is_ircgrad:
            for i in range(len(self.grad)):
                self.comments[i] += ' Grad= %s'%(self.grad[i])
        """

        # Sort x, ces, geoms, and cgrads along x
        mapd = ['x','ces','geoms']
        if is_ircgrad:
            mapd.append('cgrad')
        self.sortAlongX(mapd)
        """
        For ElectronicStructure objects, geometries will be shown
        in the order as they appear in the input file.
        For XYZ, if scan/irc, geometries are sorted by scanned
        parameter or reaction coordinate
        """

        # Make a plot
        y = [self.ces,]
        if is_ircgrad:
            xlabel = 'IRC coord (red, sqrt(amu)*Bohr) and gradient (green)'
            y.append(self.cgrad)
        else:
            xlabel = 'IRC coord (sqrt(amu)*Bohr)'
        s = self.plot(xlabel,x=self.x,y=y)

        if is_ircgrad:
            s += self.extrema(title='IRC remarkable points (min_grads):',yg=self.cgrad,show_max=False,frame_names=self.x,frame_prefix='IRC=')
        if self.settings.textirc:
            s += textirc(self.x,self.ces)
        return s


    def textirc(self,xs,ys):
        s = ''
        for x,y in zip(xs,ys):
            s += "%.3f %.2f\n" % (x, y) + web.br
        return s


    def textDirection(self):
        irc_dir = {-1:'Reverse',1:'Forward'}
        if self.both:
            return 'Reverse + Forward'
        else:
            return irc_dir[self.direction]


    def normalizeGradients(self,mx):
        if max(self.grad)>0:
            ratio = mx / max(self.grad)
        else:
            ratio = 1.
        yg = list(self.grad)
        for i in range(len(yg)):
            yg[i] *= ratio
        return yg
