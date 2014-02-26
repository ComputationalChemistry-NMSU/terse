if __name__ == "__main__":
    import sys,os
    append_path = os.path.abspath(sys.argv[0])[:-20]
    print "Append to PYTHONPATH: %s" % (append_path)
    sys.path.append(append_path)

import re
import math
import Tools.web as web
from Tools.BetterFile import BetterFile
import ChemicalInfo
from Geometry import Scan,IRC,Geom,ListGeoms
from ElStr import ElectronicStructure
from Containers import AtomicProps,Topology
from Parsers.NBO import NBO

import logging
log = logging.getLogger(__name__)


#TODO take advantages from BetterFile

class Gaussian(ElectronicStructure):
    """
    Gaussian 09 parser
    Analyzes a multiple-step calculation
    """

    def __init__(self):
        """
        Declares steps (type List)
        """
        self.steps = []


    def parse(self):
        """
        Parses Gaussian log file, step by step
        """

        try:
            FI = BetterFile(self.file)
            log.debug('%s was opened for reading' %(self.file))
        except:
            log.error('Cannot open %s for reading' %(self.file))

        while True:
            step = GauStep(FI)
            step.parse()
            step.postprocess()
            #print step
            if step.blanc:
                break
            self.steps.append(step)

        FI.close()
        log.debug('%s parsed successfully' % (self.file))
        return


    def webData(self):
        """
        Returns 2 strings with HTML code
        """

        we = self.settings.Engine3D()

        b1,b2,bb1,bb2,i = '','','','',1
        MaxGeoms, n_Freq = 0, 0
        b1s = []
        for step in self.steps:
            MaxGeoms = max(MaxGeoms,len(step.geoms))
            if step.vector:
                n_Freq = i
            self.settings.subcounter += 1
            step.statfile = self.settings.realPath('.stat')
            b1, b2 = step.webData(StartApplet=False)
            labeltext = '%s: %s' %(step.JobType,step.lot)
            b1s.append([b1,labeltext.upper()])
            bb2 += b2
            i += 1

        if b1s:
            bb1 = we.JMolApplet(ExtraScript = b1s[n_Freq-1][0])
            if MaxGeoms > 1:
                bb1 += web.brn + we.MultipleGeoms()
            if n_Freq:
                bb1 += web.brn + we.Vibration()
            if len(b1s)>1:
                #b1s[n_Freq-1].append('check')
                bb1 += web.brn*2
                for b1 in b1s:
                    bb1 += we.JMolButton(*b1)
                #bb1 += web.brn + we.JMolMenu(b1s)

        log.debug('webData generated successfully')
        return bb1, bb2


    def usage(self):
        for step in self.steps:
            step.usage()





class GauStep(ElectronicStructure):
    """
    Works with a single calculation step
    """


    def parse(self):
        """
        Actual parsing happens here
        """

        rc = {
                '/' : re.compile('(\S*\/\S+)'),
                'iop' : re.compile('iop\((.*?)\)'),
                'scrf-solv': re.compile('scrf.*solvent\s*=\s*(\w+)',re.IGNORECASE),
                's2' : re.compile(' S\*\*2 before annihilation\s+(\S+),.*?\s+(\S+)$'),
                'nbo-bond' : re.compile('\) BD \(.*\s+(\S+)\s*-\s*\S+\s+(\S+)'),
                'basis-fn' : re.compile('^ AtFile\(1\):\s+(.*?).gbs'),
                'chk' : re.compile('^ %%chk\s*=\s*(\S+)'),
                'charge-mult' : re.compile('^ Charge =\s+(\S+)\s+Multiplicity =\s+(\S+)'),
                'scf done' : re.compile('^ SCF Done.*?=\s+(\S+)'),
                'qcisd_t' : re.compile('^ QCISD\(T\)=\s*(\S+)'),
                'scf_conv' : re.compile('^ E=\s*(\S+)'),
                'scf_iter' : re.compile('^ Iteration\s+\S+\s+EE=\s*(\S+)'),
                'ci_cc_conv' : re.compile('^ DE\(Corr\)=\s*\S+\s*E\(CORR\)=\s*(\S+)'),
                'xyz' : re.compile('^\s+\S+\s+(\S+).*\s+(\S+)\s+(\S+)\s+(\S+)\s*$'),
                'scan param' : re.compile('^ !\s+(\S+)\s+(\S+)\s+(\S+)\s+Scan\s+!$'),
                'frozen' : re.compile('^ !\s+(\S+)\s+(\S+)\s+\S+\s+frozen.*!$',re.IGNORECASE),
                'alnum' : re.compile('[a-zA-Z]'),
                'ifreq' : re.compile('\d+\s+\d+\s+(\S+)\s+(\S+)\s+(\S+)'),
                'excited state' : re.compile('^ Excited State\s+(.*?):.*?\s+(\S+)\s*nm  f=\s*(\S+)'),
                'scan' : re.compile('Scan\s+!$')
        }
        self.chash = {}
        self.chash['NPA']      = {'Entry': 'XXX-XXX', 'Stop': 'XXX-XXX'}
        self.chash['NPA_spin'] = {'Entry': 'XXX-XXX', 'Stop': 'XXX-XXX'}
        self.chash['APT']      = {'Entry' : 'APT atomic charges:',                                                   'Stop' : 'Sum of APT' }
        self.chash['Mulliken'] = {'Entry' : 'Mulliken atomic charges:',                                              'Stop' : 'Sum of Mulliken' }
        lot_nobasis = (
                'cbs-qb3','cbs-4m','cbs-apno',
                'g1', 'g2', 'g2mp2', 'g3', 'g3mp2', 'g3b3', 'g3mp2b3', 'g4', 'g4mp2', 'g3mp2b3',
                'w1u', 'w1bd', 'w1ro',
                'b1b95', 'b1lyp', 'b3lyp', 'b3p86', 'b3pw91', 'b95', 'b971', 'b972', 'b97d', 'b98', 'bhandh', 'bhandhlyp', 'bmk', 'brc', 'brx', 'cam-b3lyp', 'g96', 'hcth', 'hcth147', 'hcth407', 'hcth93', 'hfb', 'hfs', 'hse2pbe', 'hseh1pbe', 'hsehpbe', 'kcis', 'lc-wpbe', 'lyp', 'm06', 'm062x', 'm06hf', 'm06l', 'o3lyp', 'p86', 'pbe', 'pbe', 'pbe1pbe', 'pbeh', 'pbeh1pbe', 'pkzb', 'pkzb', 'pw91', 'pw91', 'tpss', 'tpssh', 'v5lyp', 'vp86', 'vsxc', 'vwn', 'vwn5', 'x3lyp', 'xa', 'xalpha', 'mpw', 'mpw1lyp', 'mpw1pbe', 'mpw1pw91', 'mpw3pbe', 'thcth', 'thcthhyb', 'wb97', 'wb97x', 'wb97xd', 'wpbeh',
                'mp2', 'mp3', 'mp4', 'mp5', 'b2plyp', 'mpw2plyp',
                'ccd','ccsd','ccsd(t)','cid','cisd','qcisd(t)','sac-ci',
                'am1','pm3','pm6','cndo','dftba','dftb','zindo','indo',
                'amber','dreiding','uff',
                'rhf','uhf','hf','casscf','gvb',
        )
        def_basis = (
            '3-21g', '6-21g', '4-31g', '6-31g', '6-311g',
            'd95v', 'd95', 'shc',
            'cep-4g', 'cep-31g', 'cep-121g',
            'lanl2mb', 'lanl2dz', 'sdd', 'sddall',
            'cc-pvdz', 'cc-pvtz', 'cc-pvqz', 'cc-pv5z', 'cc-pv6z',
            'svp', 'sv', 'tzvp', 'tzv', 'qzvp',
            'midix', 'epr-ii', 'epr-iii', 'ugbs', 'mtsmall',
            'dgdzvp', 'dgdzvp2', 'dgtzvp', 'cbsb7',
            'gen','chkbasis',
        )
        self.irc_direction, self.irc_both = 1, False
        self.all_coords = {}
        t_ifreq_done = False
        basis_FN = ''

        # ------- Helper functions --------
        def inroute(lst,s,add=False):
            result = ''
            for si in lst:
                for sj in s.split():
                    if si.lower()==sj.lower() or ('u'+si.lower())==sj.lower() or ('r'+si.lower())==sj.lower():
                        if add:
                            result += ' '+si
                        else:
                            return si
            return result
        #
        def floatize(x):
            if '****' in x:
                return 10.
            return float(x)
        # //----- Helper functions --------


        s = 'BLANC' # It got to be initialized!
        for s in self.FI:
            s = s.rstrip()

            #
            # Try to save some time by skipping parsing of large noninformative blocks of output
            #
            try:
                # Skip parsing of SCF iterations
                if s.find(' Cycle')==0:
                    while not s == '':
                        s = self.FI.next().rstrip()
            except:
                log.warning('Unexpected EOF in the SCF iterations')
                break
            try:
                # Skip parsing of distance matrices
                if s.find('Distance matrix (angstroms):')==20:
                    n = len(self.all_coords[coord_type]['all'][-1])
                    m = int(math.ceil(n / 5.))
                    k = n % 5
                    n_lines_to_skip = m*(n + k + 2)/2
                    for i in range(n_lines_to_skip):
                        s = self.FI.next()
                    s = s.rstrip()
            except:
                log.warning('Unexpected EOF in the matrix of distances')
                break

            #
            # ---------------------------------------- Read in cartesian coordinates ----------------------------------
            #
            # Have we found coords?
            enter_coord = False
            if ' orientation:' in s:
                coord_type = s.split()[0]
                enter_coord = True
            if s.find('                Cartesian Coordinates (Ang):')==0:
                coord_type = 'Cartesian Coordinates (Ang)'
                enter_coord = True
            # If yes, then read them
            if enter_coord:
                try:
                    # Positioning
                    dashes1 = self.FI.next()
                    title1  = self.FI.next()
                    title2  = self.FI.next()
                    dashes2 = self.FI.next()
                    s = self.FI.next()
                    # Read in coordinates
                    geom = Geom()
                    atnames = []
                    while not '-------' in s:
                        xyz = s.strip().split()
                        try:
                            ati, x,y,z = xyz[1], xyz[-3],xyz[-2],xyz[-1]
                        except:
                            log.warning('Error reading coordinates:\n%s' % (s))
                            break
                        atn = ChemicalInfo.at_name[int(ati)]
                        atnames.append(atn)
                        geom.coord.append('%s %s %s %s' % (atn,x,y,z))
                        s = self.FI.next()
                    # Add found coordinate to output
                    pc = AtomicProps(attr='atnames',data=atnames)
                    geom.addAtProp(pc,visible=False) # We hide it, because there is no use to show atomic names for each geometry using checkboxes

                    if not coord_type in self.all_coords:
                        self.all_coords[coord_type] = {'all':ListGeoms(),'special':ListGeoms()}
                    self.all_coords[coord_type]['all'].geoms.append(geom)
                except StopIteration:
                    log.warning('EOF while reading geometry')
                    break

            #
            # ------------------------------------------- Route lines -------------------------------------------------
            #
            if s.find(' #')==0:
                # Read all route lines
                s2 = s
                while not '-----' in s2:
                    self.route_lines += s2[1:]
                    try:
                        s2 = self.FI.next().rstrip()
                    except StopIteration:
                        log.warning('EOF in the route section')
                        break
                self.route_lines = self.route_lines.lower()
                self.iop = rc['iop'].findall(self.route_lines)
                self.route_lines = re.sub('iop\(.*?\)','',self.route_lines) # Quick and dirty: get rid of slash symbols

                # Get Level of Theory
                # Look for standard notation: Method/Basis
                lot = rc['/'].search(self.route_lines)
                # print self.route_lines
                if lot:
                    self.lot, self.basis = lot.group(1).split('/')
                    if self.basis == 'gen' and basis_FN: # Read basis from external file
                        self.basis = basis_FN
                else:
                    # Look for method and basis separately using predefined lists of standard methods and bases
                    lt = inroute(lot_nobasis,self.route_lines)
                    if lt:
                        self.lot = lt
                    bs = inroute(def_basis,self.route_lines)
                    if bs:
                        self.basis = bs

                # Extract %HF in non-standard functionals
                for iop in self.iop:
                    if '3/76' in iop:
                        encrypted_hf = iop.split('=')[1]
                        str_hf = encrypted_hf[-5:]
                        num_hf = float(str_hf[:3]+'.'+str_hf[3:])
                        self.lot_suffix += '(%.2f %%HF)' %(num_hf)

                # Read solvent info
                if 'scrf' in self.route_lines:
                    solvent = rc['scrf-solv'].search(self.route_lines)
                    if solvent:
                        self.solvent = solvent.group(1)

                # Get job type from the route line
                self.route_lines = re.sub('\(.*?\)','',self.route_lines) # Quick and dirty: get rid of parentheses to get a string with only top level commands
                self.route_lines = re.sub('=\S*','',self.route_lines) # Quick and dirty: get rid of =... to get a string with only top level commands
                jt = inroute(('opt','freq','irc'),self.route_lines) # Major job types
                if jt:
                    self.JobType = jt
                self.JobType += inroute(('td','nmr','stable'),self.route_lines,add=True) # Additional job types

            # Recognize job type on the fly
            if ' Berny optimization' in s and self.JobType=='sp':
                self.JobType = 'opt'
            if rc['scan'].search(s):
                self.JobType = 'scan'

            #
            # ---------------------------------------- Read archive section -------------------------------------------
            #
            if 'l9999.exe' in s and 'Enter' in s:
                try:
                    while not '@' in self.l9999:
                        s2 = self.FI.next().strip()
                        if s2=='':
                            continue
                        self.l9999 += s2
                except StopIteration:
                    log.warning('EOF while reading l9999')
                    break
                #print self.l9999

                la = self.l9999.replace('\n ','').split('\\')

                if len(la)>5:
                    self.machine_name = la[2]
                    if la[5]:
                        self.basis = la[5]
                    #basis = la[5]
                    #if basis == 'gen':
                        #if basis_FN:
                            #self.basis = ' Basis(?): ' + basis_FN
                        #elif not self.basis:
                            #self.basis = ' Basis: n/a'
                    self.lot = la[4]
                    self.JobType9999 = la[3]
                    if self.JobType != self.JobType9999.lower():
                        self.JobType += "(%s)" % (self.JobType9999.lower())


            #
            # ---------------------------------------- Read simple values ---------------------------------------------
            #

            #Nproc
            if s.find(' Will use up to') == 0:
                self.n_cores = s.split()[4]


            # time
            if s.find(' Job cpu time:') == 0:
                s_splitted = s.split()
                try:
                    n_days = float(s_splitted[3])
                    n_hours = float(s_splitted[5])
                    n_mins = float(s_splitted[7])
                    n_sec = float(s_splitted[9])
                    self.time = n_days*24 + n_hours + n_mins/60 + n_sec/3600
                except:
                    self.time = '***'


            # n_atoms
            if s.find('NAtoms=') == 1:
                s_splitted = s.split()
                self.n_atoms = int(s_splitted[1])

            # n_basis
            if s.find('basis functions') == 7:
                s_splitted = s.split()
                self.n_primitives = int(s_splitted[3])

            # Basis
            if s.find('Standard basis:') == 1:
                self.basis = s.strip().split(':')[1]

            # n_electrons
            if s.find('alpha electrons') == 7:
                s_splitted = s.split()
                n_alpha = s_splitted[0]
                n_beta = s_splitted[3]
                self.n_electrons = int(n_alpha) + int(n_beta)


            # S^2
            if s.find(' S**2 before annihilation')==0:
                s_splitted = s.split()
                before = s_splitted[3][:-1]
                after = s_splitted[5]
                self.s2 = before + '/' + after
                for ct in self.all_coords.values():
                    if ct['all']:
                        ct['all'][-1].addProp('s2',self.s2)

            # CBS-QB3
            if ' CBS-QB3 Enthalpy' in s:
                self.extra += s

            # Solvent
            if ' Solvent              :' in s:
                self.solvent = s.split()[2][:-1]
            # Solvation model
            if not self.solv_model and 'Model                :' in s:
                self.solv_model = s.strip().split()[2]

            # Try to guess basis name from the file name
            if not basis_FN:
                bas_FN = rc['basis-fn'].match(s)
                if bas_FN:
                    basis_FN = re.sub('.*\/','',bas_FN.group(1))

            # Read Checkpoint file name
            if not self.chk:
                chk = rc['chk'].match(s)
                if chk:
                    self.chk = chk.group(1)

            # Read Symmetry
            if ' Full point group' in s:
                self.sym = s.split()[3]

            # Read charge_multmetry
            if not self.charge:
                charge_mult = rc['charge-mult'].match(s)
                if charge_mult:
                    self.charge = charge_mult.group(1)
                    self.mult   = charge_mult.group(2)

            # Collect WF convergence
            #scf_conv = rc['scf_conv'].match(s)
            #if not scf_conv:
                #scf_conv = rc['scf_iter'].match(s)
            #if scf_conv:
                #self.scf_conv.append(scf_conv.group(1))

            # Read Converged HF/DFT Energy
            scf_e = rc['scf done'].match(s)
            if scf_e:
                if s[14]=='U':
                    self.openShell = True
                self.scf_e = float(scf_e.group(1))
                self.scf_done = True
                for ct in self.all_coords.values():
                    if ct['all']:
                        ct['all'][-1].addProp('e', self.scf_e) # TODO Read in something like self.best_e instead!

            #CI/CC
            if not self.ci_cc_done:
                if ' CI/CC converged in' in s:
                    self.ci_cc_done = True
            if ' Largest amplitude=' in s:
                self.amplitude = s.split()[2].replace('D','E')

            # CI/CC Convergence
            ci_cc_conv = rc['ci_cc_conv'].match(s)
            if ci_cc_conv:
                x  = float(ci_cc_conv.group(1))
                self.ci_cc_conv.append(x)
            """
            Do we really need to parse post-hf energies?
            # Read post-HF energies
            if ' EUMP2 = ' in s:
                self.postHF_lot.append('MP2')
                self.postHF_e.append(s.split()[-1])
            # QCISD(T)
            qcisd_t = rc['qcisd_t'].match(s)
            if qcisd_t:
                self.postHF_lot.append('QCISD(T)')
                self.postHF_e.append(qcisd_t.group(1))
            """

            """
            #XXX Probably, we don't need it at all as more reliable topology can be read from NBO output
            # Read in internal coordinates topology
            if '! Name  Definition              Value          Derivative Info.                !' in s:
                dashes = self.FI.next()
                s = self.FI.next().strip()
                while not '----' in s:
                    self.topology.append(s.split()[2])
                    s = self.FI.next().strip()
            """
            #
            # ------------------------------------- NBO Topology ----------------------------------- 
            #
            if 'N A T U R A L   B O N D   O R B I T A L   A N A L Y S I S' in s:
                nbo_analysis = NBO()
                nbo_analysis.FI = self.FI
                nbo_analysis.parse()
                nbo_analysis.postprocess()
                self.topologies.append(nbo_analysis.topology) # Actually, we save a reference, so we can keep using nbo_top
                for ct in self.all_coords.values():
                    if ct['all']:
                        last_g = ct['all'][-1]
                        last_g.nbo_analysis = nbo_analysis
                        last_g.addAtProp(nbo_analysis.charges)
                        if nbo_analysis.OpenShell:
                            last_g.addAtProp(nbo_analysis.spins)

            #
            # ------------------------------------- Charges ------------------------------------- 
            #
            try:
                for ch in self.chash.keys():
                    if self.chash[ch]['Entry'] in s:
                        pc = AtomicProps(attr=ch)
                        self.FI.next()
                        s = self.FI.next()
                        while not self.chash[ch]['Stop'] in s:
                            c = s.strip().split()[2]
                            pc.data.append(float(c))
                            s = self.FI.next()
                        for ct in self.all_coords.values():
                            if ct['all']:
                                ct['all'][-1].addAtProp(pc)
            except StopIteration:
                log.warning('EOF while reading charges')
                break


            #
            # --------------------------------------------- Opt -------------------------------------------------------
            #
            if 'opt' in self.JobType:
                if '         Item               Value     Threshold  Converged?' in s:
                    self.opt_iter += 1
                    try:
                        for conv in ('max_force','rms_force','max_displacement','rms_displacement'):
                            s = self.FI.next()
                            x, thr = floatize(s[27:35]), float(s[40:48])
                            conv_param = getattr(self,conv)
                            conv_param.append(x-thr)
                            for ct in self.all_coords.values():
                                if ct['all']:
                                    ct['all'][-1].addProp(conv, x-thr)
                    except:
                        log.warngin('EOF in the "Converged?" block')
                        break
                if '    -- Stationary point found.' in s:
                    self.opt_ok = True

            #
            # --------------------------------------------- IRC -------------------------------------------------------
            #
            if 'irc' in self.JobType:
                # IRC geometry was just collected?

                if 'Magnitude of analytic gradient =' in s:
                    self.grad = float(s.split('=')[1])

                if 'Rxn path following direction =' in s:
                    if 'Forward' in s:
                        self.irc_direction = 1
                    if 'Reverse' in s:
                        self.irc_direction = -1

                """
                b_optd = ('Optimized point #' in s) and ('Found' in s)
                b_deltax = '   Delta-x Convergence Met' in s
                b_flag = 'Setting convergence flag and skipping corrector integration' in s
                t_irc_point = b_optd or b_deltax or b_flag
                """

                """
                G03:
                Order of IRC-related parameters:
                    1. Geometry,
                    2. Energy calculated for that geometry
                    3. Optimization convergence test
                G09:
                For IRC, there is a geometry entry right before the 'NET REACTION COORDINATE' string,
                and energy has not been attached to it yet, so we do it manually
                """
                if 'NET REACTION COORDINATE UP TO THIS POINT =' in s:
                    x = float(s.split('=')[1])
                    for ct in self.all_coords.values():
                        if ct['all']:
                            girc = ct['all'][-1]
                            girc.addProp('x', x*self.irc_direction)
                            girc.addProp('e', self.scf_e)
                            if '/' in str(self.s2):
                                girc.addProp('s2', self.s2.split('/')[1].strip())
                            ct['special'].geoms.append(girc)

                if 'Minimum found on this side of the potential' in s\
                    or 'Beginning calculation of the REVERSE path' in s:
                    self.irc_direction *= -1
                    self.irc_both = True

            #
            # -------------------------------------------- Scan -------------------------------------------------------
            #
            if 'scan' in self.JobType:
                """
                Order of scan-related parameters:
                    1. Geometry,
                    2. Energy calculated for that geometry
                    3. Optimization convergence test
                If Stationary point has been found, we already have geometry with energy attached as prop, so we just pick it up
                """
                # Memorize scan geometries
                if '    -- Stationary point found.' in s:
                    for ct in self.all_coords.values():
                        if ct['all']:
                            ct['special'].geoms.append(ct['all'][-1])
                # Record scanned parameters
                for param in  self.scan_param_description.values():
                    if ' ! ' in s and param in s:
                        x = float(s.split()[3])
                        for ct in self.all_coords.values():
                            if ct['special']:
                                ct['special'][-1].addProp(param,x)
                # Keep extended information about scanned parameter
                sc = rc['scan param'].match(s)
                if sc:
                    param, param_full = sc.group(1), sc.group(2)
                    self.scan_param_description[param] = param_full

            #
            # ------------------------------------- Scan or Opt: Frozen parameters -------------------------------------
            #
            if 'scan' in self.JobType or 'opt' in self.JobType:
                sc = rc['frozen'].match(s)
                if sc:
                    self.frozen[sc.group(1)] = sc.group(2)

            #
            # ------------------------------------------ Freqs --------------------------------------------------------
            #
            if 'freq' in self.JobType or 'opt' in self.JobType:
                # T
                if ' Temperature ' in s:
                    x = float(s.split()[1])
                    self.freq_temp.append(x)
                # ZPE, H, G
                if ' Sum of electronic and zero-point Energies=' in s:
                    try:
                        x = float(s.split()[-1])
                        self.freq_zpe.append(x)
                        self.FI.next()
                        # H
                        Htherm = self.FI.next()
                        x = float(Htherm.split('=')[1])
                        self.freq_ent.append(x)
                        # G
                        Gtherm = self.FI.next()
                        x = float(Gtherm.split('=')[1])
                        self.freq_G.append(x)
                    except:
                        log.warngin('EOF in the Thermochemistry block')
                        break

                # Read in vibrational modes
                if 'Frequencies' in s:
                    for fr in s.split(' '):
                        if '.' in fr:
                            self.freqs.append(float(fr))

                # Read in imaginary frequencies
                if      (not t_ifreq_done) \
                   and (self.freqs) \
                   and (self.freqs[0]<0) \
                   and not rc['alnum'].search(s):
                       ifreq = rc['ifreq'].search(s)
                       if ifreq:
                           x, y, z = ifreq.groups()
                           self.vector.append('%s %s %s' % (x,y,z))
                       else:
                            t_ifreq_done = True

            #
            # --------------------------------------- TD --------------------------------------------------------------
            #
            if 'td' in self.JobType:
                uv = rc['excited state'].match(s)
                if uv:
                    self.n_states = uv.group(1)
                    #print self.n_states
                    l,f = float(uv.group(2)),float(uv.group(3))
                    self.uv[l] = f
                    #self.uv[uv.group(1)] = uv.group(2)

            #
            # --------------------------------------- Stable --------------------------------------------------------------
            #
            if 'stable' in self.JobType:
                if s.find(' The wavefunction has an')==0 and 'instability' in s:
                    self.extra += s

            #
            # ======================================= End of Gau Step ==================================================
            #
            if 'Normal termination of Gaussian' in s:
                self.OK = True
                break

        # We got here either 
        else:
            self.blanc = (s=='BLANC')
        return



    def postprocess(self):
        #
        # ======================================= Postprocessing  ======================================================
        #

        if self.lot_suffix:
            self.lot += self.lot_suffix

        """
        Choose coordinates to show in JMol
        Standard:
            '+' Compatible with vib. frequencies
            '-' Tends to swap each several steps, not very good for viewing
            '-' Not available when NoSym option provided
        Input:
            '-' Not compatible with vib. frequencies
            '+' Gives smooth change of geometries
        Cartesian Coordinates, Z-Matrix:
            '+' In some cases, the only coordinates given in the output file
        """
        if self.freqs and self.freqs[0]<0:
            order = ('Standard','Input','Cartesian Coordinates (Ang)','Z-Matrix')
        else:
            order = ('Input','Cartesian Coordinates (Ang)','Z-Matrix','Standard')

        n_steps_by_to = {}
        for to in order:
            if to in self.all_coords:
                nst = len(self.all_coords[to]['all'].geoms)
                if nst > self.n_steps:
                    self.n_steps = nst

        # choose geometries to show
        for tp in ('special','all'):
            for to in order:
                if to in self.all_coords and self.all_coords[to][tp]:
                    self.geoms = self.all_coords[to][tp]
                    break
            if self.geoms:
                log.debug('%s orientation used' % (to))
                break
        del self.all_coords

        if 'irc' in self.JobType:
            self.series = IRC(other=self.geoms)
            self.series.direction = self.irc_direction
            self.series.both = self.irc_both
        del self.irc_direction
        del self.irc_both

        if 'scan' in self.JobType:
            self.series = Scan(other=self.geoms)

        if self.freqs and self.geoms:
            if self.OK:
                self.geoms.geoms = [self.geoms[-1],]

        # Transfer charge from hydrogens to heavy atoms
        if self.topologies: # For now, we assume that the only possible topology is NBO
            topology = self.topologies[0] # Assumtion, might cause troubles
            if not topology:
                log.info('Cannot extract NBO topology')
            else:
                for geom in self.geoms: # Loop over geoms
                    for ap_name in geom.atprops: # Loop over  props
                        if ap_name in self.chash: # Is this prop a charge?
                            # Retrieve original charges
                            ap = getattr(geom,ap_name)
                            # Create new set of charges, where charges on H will be included to heavy atoms
                            ap_H_name = ap_name + '_H'
                            ap_H = AtomicProps(attr=ap_H_name,data=[0.0]*len(ap.data))
                            # Loop over all atoms
                            for ati in range(len(ap.data)):
                                atname = geom.atnames.data[ati]
                                if atname != 'H':
                                    ap_H.data[ati] += ap.data[ati]
                                    continue
                                top_i = str(ati + 1)
                                if not top_i in topology.data:
                                    log.info('Cannot extract NBO topology for atom '+top_i)
                                    ap_H.data[ati] += ap.data[ati]
                                    continue
                                H_connected = topology.data[top_i]
                                if len(H_connected) <> 1:
                                    log.info('Weird topology of molecule')
                                    ap_H.data[ati] += ap.data[ati]
                                    continue
                                top_heavy = int(H_connected.keys()[0])
                                heavy_at = top_heavy - 1
                                atname = geom.atnames.data[heavy_at]
                                # if atname == 'C': Can be used to condense H charges only on C atoms; however, sophisticated selection is needed to apply labels correctly; I will get back to it later
                                ap_H.data[ati] = 0.0
                                ap_H.data[heavy_at] += ap.data[ati]
                            geom.addAtProp(ap_H)

        del self.chash

        log.debug('Gaussian step (%s) parsed successfully' %(self.JobType))
        return


    def usage(self):
        s = ''
        s += 'Computation Node: %s\n' % (self.machine_name)
        if hasattr(self,'n_cores'):
            s+= '#Cores: %s\n' % (self.n_cores)
        s += 'Level of Theory: %s\n' % (self.lot)
        s += 'Job type: %s\n' % (self.JobType)
        if self.solvent:
            s += 'Solvent: %s\n' % (self.solvent)
        s += 'Open Shell: %i\n' % (self.openShell)
        s += '#Atoms: %i\n' % (self.n_atoms)
        s += '#Electrons: %i\n' % (self.n_electrons)
        s += '#Gaussian Primitives %i\n' % (self.n_primitives)
        if 'opt' in self.JobType:
            s += '#Opt Steps %s\n' % (self.n_steps)
        if 'td' in self.JobType:
            s += '#Excited States %s\n' % (self.n_states)
        s += '#SU %.1f\n' % (self.time)

        FS = open(self.statfile,'w')
        FS.write(s)
        FS.close()
        #print s


#
#
#
#
#
if __name__ == "__main__":

    DebugLevel = logging.DEBUG
    logging.basicConfig(level=DebugLevel)

    from Settings import Settings
    from Top import Top
    Top.settings = Settings(FromConfigFile = True)

    from HTML import HTML
    WebPage = HTML()
    WebPage.makeHeader()

    f = Gaussian()
    f.file = sys.argv[1]
    #import profile
    #profile.run('f.parse()')
    f.parse()
    f.postprocess()
    print f.steps[0]
    b1, b2 = f.webData()

    WebPage.makeLine(b1,b2)
    WebPage.makeTail()
    WebPage.write()
