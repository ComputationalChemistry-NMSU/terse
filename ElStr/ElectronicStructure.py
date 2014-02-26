from Top import Top
from Tools.IO import IO
import Tools.web as web
from Geometry import IRC,ListGeoms,Scan
from Containers import Topology

import logging
log = logging.getLogger(__name__)

class ElectronicStructure(Top):
    def __init__(self,FI=None):
        na = 'n/a'
        self.machine_name = ''

        self.FI = FI
        self.JobType = 'sp'
        self.lot, self.basis = '',''
        self.lot_suffix = ''
        self.route_lines, self.l9999 = '','' #G

        self.sym = 'C1'
        self.n_proc = 1
        self.n_atoms = 0
        self.n_electrons = 0
        self.n_primitives = 0
        self.charge, self.mult, self.s2 = None, None, 0
        self.openShell = False
        self.solvent, self.solv_model = '',''
        self.geoms, self.vector = ListGeoms(), []

        self.topologies = []

        self.scf_e = 0.
        self.scf_done, self.ci_cc_done = False, False
        self.postHF_lot, self.postHF_e = [], []
        self.scf_conv, self.ci_cc_conv = [], []
        self.amplitude = 0.0

        self.opt_iter = 0
        self.opt_ok = False
        self.max_force, self.rms_force = [], []
        self.max_displacement, self.rms_displacement = [], []

        self.series = None
        self.scan_param_description = {}
        self.grad = 0.
        self.frozen = {}

        self.n_steps = 0
        self.n_states = 0

        self.freq_temp, self.freq_ent, self.freq_zpe, self.freq_G = [], [], [], []
        self.freqs = []
        self.nimag = 0
        self.uv = {}

        self.comments, self.warnings, self.extra = '','',''
        self.chk = None
        self.OK = False
        self.blanc = False
        self.time = 0


    def webData(self,StartApplet=True):
        we = self.settings.Engine3D()
        io = IO()

        color = {'err':'red', 'imag':'blue', 'lot':'green'}
        b2, JmolScript = '', ''
        comments = []

        if self.JobType:
            sx = self.JobType.upper()
            if 'irc' in self.JobType:
                sx += ' ' + self.series.textDirection()
            sx = web.br + web.tag(sx,'strong')

            if self.OK:
                b2 += sx
            else:
                b2 += web.tag(sx,"SPAN style='color:%s'" % (color['err']))

        if self.lot:
            if self.basis:
                self.lot += '/' + self.basis
            b2 += web.br + web.tag(self.lot.upper(),"SPAN style='color:%s'" % (color['lot']))

        if self.solvent:
            sx = 'Solvation: '
            if self.solv_model:
                sx += '%s(%s)' % (self.solv_model, self.solvent)
            else:
                sx += self.solvent
            b2 += web.br + web.tag(sx,"SPAN style='color:%s'" % (color['lot']))

        if self.sym:
            b2 += web.br + "Symmetry: %s\n" % (self.sym)

        if self.charge:
            b2 += web.br + "Charge: %s; "  % (self.charge)

        if self.mult:
            b2 += "Mult: %s\n"  % (self.mult)

        if self.lot and not self.lot.find('R')==0:
            b2 += web.br + "S2= %s,\n"  % (self.s2)

        if self.scf_e:
            b2 += web.br +  "E_SCF= %-11.6f\n" % (self.scf_e)

        if self.amplitude:
            f_ampl = float(self.amplitude)
            s_ampl = '%.3f' % (f_ampl)
            if f_ampl >= 0.1:
                sx = web.tag(s_ampl,"SPAN style='color:%s'" % (color['err']))
            else:
                sx = s_ampl
            b2 += web.br + "Max Amplitude= %s\n" % (sx)

        # Add pics for SP 
        if 'sp' in self.JobType and not self.OK:
            wftype = ''
            if not self.ci_cc_done:
                wftype = 'ci_cc'
            if not self.scf_done:
                wftype = 'scf'
            if wftype:
                b2 += web.br + wftype + ' not converged...'
                y = getattr(self,wftype+'_conv')
                picpath = io.writePic('-sp-conv.png',xname='Step N',yname='E, '+self.settings.EnergyUnits,y=y)
                b2 += web.img(picpath)
        # Freq
        if 'freq' in self.JobType:
            # Give thermochemistry values
            for i in range(len(self.freq_temp)):
                b2 += web.br + "T=%6.2f: H= %10.6f, E+ZPE= %10.6f, G= %10.6f\n" \
                      % (self.freq_temp[i],self.freq_ent[i],self.freq_zpe[i],self.freq_G[i])
            if self.freqs:
                # Show freqs
                b2 += web.br + "Freqs: "
                # Color i-freqs
                i = 0
                while self.freqs[i] < 0:
                    s_freq = "% .1f," % (self.freqs[i])
                    if i == 0:
                        col = 'imag'
                    else:
                        col = 'err'
                    b2 += web.tag(s_freq, "SPAN style='color:%s'" % (color[col]))
                    i += 1
                b2 += "%.1f .. %.1f\n" % (self.freqs[i], self.freqs[-1])
            if self.nimag > 0:
                b2 += web.brn + web.tag('Imaginary Freq(s) found!',"SPAN style='color:%s'" % (color['imag']))

        # Frozen
        if self.frozen:
            frs = self.frozen.values()
            self.extra += web.br + 'Frozen parameters detected (highlighted with measurement lines)'
            JmolScript += we.measureGau(frs)
            if len(frs)>3:
                JmolScript += 'set measurementlabels off;'
        # Opt
        if 'opt' in self.JobType:
            b2 += web.br + web.tag('NOpt=%i' % (self.opt_iter),'em')
            if not self.opt_ok:
                b2 += web.br + "Stationary Point not found!\n"
            if (not self.OK) or self.settings.FullGeomInfo:
                sg = self.geoms
                y = [sg.toBaseLine(), sg.max_force, sg.rms_force, sg.max_displacement, sg.rms_displacement]
                ylabel = 'E, %s' % (self.settings.EnergyUnits)
                picpath = io.writePic('-opt-conv.png',
                        xname='Step N',yname=ylabel,
                        keys=['E','Max Force', 'RMS Force', 'Max Displacement', 'RMS Displacement'],
                        y=y,ny2=4
                        )
                b2 += web.img(picpath)
                #b2 += self.geoms.plot(xlabel='Opt point')
        # IRC
        if 'irc' in self.JobType:
            b2 += self.series.webData()
            comments = self.series.comments

        # Scan
        if 'scan' in self.JobType:
            #print self.series.props
            b2 += self.series.webData()
            JmolScript += we.measureGau(self.series.props)

        # TD DFT
        if 'td' in self.JobType and self.uv:
            b2 += web.brn + web.tag('UV Spectra','em') + web.brn
            for w in sorted(self.uv):
                #if w > 1000.:
                if self.uv[w] > 0.01:
                    b2 += "%s %s\n" % (w, self.uv[w]) + web.brn
            b2 += web.brn

        #
        # Charges
        # 
        sx = ''
        for i in range(len(self.geoms)):
            g = self.geoms[i]
            if g.atprops:
                sx += 'Structure %i: ' % (i+1)
                for ap in g.atprops:
                    sx += getattr(g,ap).webData()
                sx += we.JMolButton('label off;color atoms cpk','Off') + web.brn
            if self.settings.full and hasattr(g,'nbo_analysis'):
                nbo_b1,nbo_b2 = g.nbo_analysis.webData()
                sx += nbo_b2
        b2 += web.brn + sx

        # NBO Topology
        nbobonds = ''
        bo = ('-','S','D','T','Q')
        if self.topologies:
            pass
            # TODO write this topology to MOL file
            #for i in self.nbo_topology:
                #for j in self.nbo_topology[i]:
                    #nbobonds += "%s %s %s " % (bo[self.nbo_topology[i][j]],i,j)
        if self.comments:
            b2 += web.br +  web.tag('Comments','strong') + ":%s\n" % self.comments

        if self.warnings:
            b2 += web.br +  web.tag('Warnings','strong') + ":%s\n" % self.warnings

        if self.extra:
            b2 += web.br + web.tag(self.extra,'em')

        b2 += web.br



        #
        # ----- b1 -----
        #
        #if self.nbo_topology and not self.vectors:
        wp = self.geoms.write(fname='.xyz', vectors=self.vector)
        labeltext = '%s: %s' %(self.JobType,self.lot)

        if StartApplet:
            JmolScript += '; ' + we.JMolText(label=labeltext.upper(),script=False)
            #JmolScript += '; ' + we.JMolText(label='model %{_modelNumber}',position='bottom left', script=False)
            JmolScript += '; ' + we.JMolText(label='model _modelNumber',position='bottom left', script=False)
            b1 = we.JMolApplet(webpath=wp, ExtraScript = JmolScript)
            b1 += web.brn + we.JMolCommandInput()
            if len(self.geoms)>1:
                b1 += web.brn + we.MultipleGeoms()
        else:
            b1 = we.JMolLoad(webpath=wp, ExtraScript=JmolScript)
            b1 += '; ' + we.JMolText(label=labeltext.upper(),script=False)
            #b1 += '; ' + we.JMolText(label='model %{_modelNumber}',position='bottom left', script=False)
            b1 += '; ' + we.JMolText(label='model _modelNumber',position='bottom left', script=False)

        log.debug('webData for Gaussian step generated successfully')
        return b1, b2


