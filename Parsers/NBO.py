if __name__ == "__main__":
    import sys,os
    selfname = sys.argv[0]
    full_path = os.path.abspath(selfname)[:]
    last_slash = full_path.rfind('/')
    dirpath = full_path[:last_slash] + '/..'
    print "Append to PYTHONPATH: %s" % (dirpath)
    sys.path.append(dirpath)

import time,re,logging
import math
from Tools import web
from Tools.BetterFile import BetterFile
from Top import Top
from Containers import Topology, AtomicProps
log = logging.getLogger(__name__)

#TODO Enable to parse .nbout from the Gaussian .log file
#TODO Make the parser to return data readable by Gaussian parser (charges, spin charges, topology)
#TODO Implement the --inbo feature
#TODO Add more relevant output in .nbout file (think about desirable fields)
#TODO take care about 3-centered bonds
#TODO Standalone code; where to take geoms from?

class nbo_result(Top):
    def __init__(self):
        self.sopta    = []
        self.atoms    = []
        self.orbs     = []
        self.bonds    = []
        self.topology = Topology('NBO')
        self.NonLewis = 0.
        self.NatRydbergPop = 0.

    def webData(self):
        s = ''
        for sopta in self.sopta:
            if float(sopta.e2) > 10.0:
                s += '%15s --> %15s: %s' % (sopta.donor.sorb, sopta.acceptor.sorb, sopta.e2)
                s += web.brn
        return s

    def atomByID(self,i):
        atnames = map(lambda k: k.idx, self.atoms)
        ati = atnames.index(i.strip())
        return self.atoms[ati]

    def nboByID(self,i):
        nbonames = map(lambda k: k.idx, self.orbs)
        nboi = nbonames.index(i.strip())
        return self.orbs[nboi]

    def read_atomic_info(self,FI):
        log.debug('Start: line %s',FI.lnum)
        FI.skip_until('Natural atomic orbital occupancies',Offset=4)
        while True:
            d = FI.getBlock()
            FI.skip()
            try:
                int(d[-1][:4])
            except:
                break
            atom = nbo_atom()
            atom.parse(d)
            self.atoms.append(atom)

        # Read in atomic charges
        d = FI.getBlock(StartMatch='Summary of Natural Population Analysis',StartOffset=6,EndMatch='===')
        for s in d:
            ss = s.split()
            if ss[0].lower()=='bq':
                bq = nbo_atom(idx=ss[1])
                bq.symbol = 'Bq'
                self.atoms.append(bq)
                continue
            at = self.atomByID(ss[1])
            at.charge, at.core, at.valence, at.rydberg = ss[2:6]
        self.atoms.sort(key=lambda at:int(at.idx))
        log.debug('Done: line %s',FI.lnum)



class nbo_sopta(Top):
    def __init__(self):
        self.donor = None
        self.acceptor = None
        self.e2 = 0.0
        self.F_ij = 0.0
        self.de = 0.0

    def parse(self,rs,nr):
        norb1,norb2,e2,de,f_ij = rs.groups()
        self.donor = nr.nboByID(norb1)
        self.acceptor = nr.nboByID(norb2)
        self.e2, self.de, self.f_ij = e2,de,f_ij



class nbo_atom(Top):
    def __init__(self,idx = 0):
        self.idx = idx
        self.symbol = ''
        self.naturalElectronicConfiguration = ''
        self.charge = 0.
        self.core = 0.
        self.valence = 0.
        self.rydberg = 0.
        self.num_nao = 0.

    def parse(self,d):
        self.symbol, self.idx, hm = d[-1].split()[1:4]
        # Get highest angular momentum of the atom
        hms = ('s','p','d','f','g')
        hm_char = hm[0].lower()
        self.momenta = hms[:hms.index(hm_char)+1]
        self.num_nao = len(d)



class nbo_orb(Top):
    def __init__(self,idx=0,sorb=''):
        self.idx = idx
        self.sorb = sorb
        self.nbo_type = '' # BD/BD*/CR/LP/
        self.nhos = []
        self.pop = 0.0
        self.bond_bending = 0.0
        self.chk_index = 0

    def parse(self,FI,nr):
        ss = FI.s.rstrip()
        self.idx, self.pop, self.sorb = re.search('(\S+)\.\s+\((.*?)\)\s*(.*?)\s*(?:s|$)',ss).groups()
        self.nbo_type = self.sorb[:3]
        if re.search('CR|LP|RY',self.nbo_type):
            # One-center orbital
            nho = nbo_nho()
            nho.parse(FI,nr,OneCenter=True)
            self.nhos.append(nho)
        else:
            # Several-center orbitals
            # Loop over NHOs
            FI.skip()
            while FI.s.strip():
                if re.search('^\s+\d+\.\s+',FI.s):
                    break
                nho = nbo_nho()
                nho.parse(FI,nr,OneCenter=False)
                self.nhos.append(nho)



class nbo_nho(Top):
    def __init__(self,idx=0,sorb=''):
        self.idx = idx
        self.sorb = sorb
        self.at = None
        self.c = 0.0
        self.s = 1.0
        self.p = ''
        self.d = ''
        self.f = ''
        self.naos = []

    def parse(self,FI,nr,OneCenter):
        if OneCenter:
            self.c, at_id = 1.0, re.search('\D+(\d+)\s*s',FI.s).groups()[0]
        else:
            self.c, at_id = re.search('\s+(\S+)\*.*?\D+(\d+)\s*s',FI.s).groups()
        self.at = nr.atomByID(at_id)
        self.get_p_d_f(FI,self.at)

        while not('(' in FI.s or len(FI.ssplit)==0):
            self.naos.extend(FI.ssplit)
            FI.nsplit()

    def get_p_d_f(self,FI,at):
        for m in at.momenta:
            bad = False
            if m == 'f':
                FI.next()
            rs = re.search(m+'(.*?)\(',FI.s)
            if rs:
                setattr(self,m,rs.groups()[0])
            else:
                bad = True
                break
        if bad and m == 'f':
            return
        else:
            FI.nsplit()





class NBO(Top):
    """
    NBO 3.1
    """


    def __init__(self):
        self.FI = None
        self.options = ''
        self.NBO_version = ''
        self.comments = ''
        self.setAB = nbo_result()
        self.OpenShell = False
        self.charges = AtomicProps(attr='NPA')
        self.spins = AtomicProps(attr='NPA_spin')
        self.topology = Topology('NBO')

    def parse(self):
        if self.FI:
            FI = self.FI
        else:
            FI = BetterFile(self.file)

        # Get NBO version
        FI.skip_until('***')
        self.NBO_version = re.search('\*+(.*?)\*+',FI.s).groups()[0].strip()

        # Options
        self.options = web.brn.join(FI.getBlock(StartMatch='/ : '))

        # Density
        self.comments += FI.nstrip() + web.brn

        # Job title
        FI.skip()
        title = FI.nstrip()
        self.comments = title[title.find(':')+1:].strip()

        # Read some atomic information
        self.setAB.read_atomic_info(FI)

        # Population of Rydberg orbitals
        FI.skip_until('Natural Rydberg Basis')
        self.setAB.NatRydbergPop = FI.s.split()[3]


        where = FI.skip_until(['Alpha spin orbitals','Total non-Lewis','Please check you input data','NBO analysis skipped by request'])
        # If 'Alpha spin orbitals' then redo the analysis;
        # Expect beta spin block
        if where==0:
            self.OpenShell = True
            setnames = ('setA','setB')
            log.debug('Open-shell molecule, NBO analysis will be performed separately for alpha- and beta-orbitals')
        elif where==1:
            setnames = ('setAB',)
        elif where==2:
            log.warning('Please check your NBO file')
            return
        elif where==3:
            log.info('Truncated NBO analysis detected')
            return

        # Here, start a huge loop over A/B sets (or just an A+B set if we have closed-shell)
        for rSet in setnames:
            if self.OpenShell:
                setattr(self,rSet,nbo_result())
                nr = getattr(self,rSet)

                nr.read_atomic_info(FI)
                FI.skip_until('Natural Rydberg Basis')
                nr.NatRydbergPop = FI.s.split()[3]
            else:
                nr = self.setAB

            # Read in non-Lewis population
            if not FI.skip_until(['NBO analysis skipped by request','Total non-Lewis']):
                continue
            nr.NonLewis = FI.s.split()[2]

            # Read in NBOs
            FI.skip_until('Bond orbital/ Coefficients/ Hybrids',Offset=2)
            while FI.s.rstrip():
                nbo = nbo_orb()
                nbo.parse(FI,nr)
                nr.orbs.append(nbo)

            # Read in directionality
            d = FI.getBlock(StartMatch='NHO Directionality and "Bond Bending"',StartOffset = 10)
            for s in d:
                rs = re.search('^\D*(\d+)\.(?:.*?\.){4}.\s+(\S+).*?\s+(\S+)$',s)
                if rs:
                    nbo_id, h1_dev, h2_dev = rs.groups()
                    nbo = nr.nboByID(nbo_id)
                    nbo.nhos[0].bond_bending = h1_dev
                    nbo.nhos[1].bond_bending = h2_dev

            # Second order perturbation analysis
            d = FI.getBlock(
                        StartMatch = 'Second Order Perturbation Theory Analysis of Fock Matrix in NBO Basis', StartOffset = 9,
                        EndMatch = 'Natural Bond Orbitals (Summary):'
                    )
            for s in d:
                rs = re.search('^\D*(\d+)\..*?\D+(\d+)\..*?(\S+)\s+(\S+)\s+(\S+)$',s)
                if not rs:
                    continue
                sopta = nbo_sopta()
                sopta.parse(rs,nr)
                nr.sopta.append(sopta)

            # Trying to understand where we are at
            try:
                i = FI.skip_until(['Leave Link  607','Reordering of NBOs for storage','Beta  spin orbitals'])
            except StopIteration:
                # EOF reached
                break
            if i==1:
                d = FI.getBlock(EndMatch='Labels of output orbitals')
                reordered = []
                for s in d:
                    colon_pos = s.find(':')+1
                    reordered.extend(s[colon_pos:].strip().split())
                for i in range(len(reordered)):
                    i_mo = str(i+1)
                    i_nbo = reordered[i]
                    nbo = nr.nboByID(i_nbo)
                    nbo.chk_index = i_mo
        return



    def postprocess(self):
        if self.OpenShell:
            for rSet in ('setA','setB'):
                nr = getattr(self,rSet)
                # Bonding topology: sum of A and B spin NBO analyses
                for orb in nr.orbs:
                    if orb.nbo_type != 'BD*':
                        continue
                    s_at1 = orb.nhos[0].at.idx.strip()
                    s_at2 = orb.nhos[1].at.idx.strip()
                    self.topology.increaseOrder(s_at1,s_at2)
                    self.topology.increaseOrder(s_at2,s_at1)

            chargesA = map(lambda a: float(a.charge), self.setA.atoms)
            chargesB = map(lambda a: float(a.charge), self.setB.atoms)
            for i in range(len(chargesA)):
                self.charges.data.append(chargesA[i] + chargesB[i])
                self.spins.data.append(  chargesA[i] - chargesB[i])
        else:
            for orb in self.setAB.orbs:
                if orb.nbo_type != 'BD*':
                    continue
                s_at1 = orb.nhos[0].at.idx.strip()
                s_at2 = orb.nhos[1].at.idx.strip()
                self.topology.increaseOrder(s_at1,s_at2)
                self.topology.increaseOrder(s_at2,s_at1)
            self.charges.data = map(lambda a: float(a.charge), self.setAB.atoms)
        return



    def webData(self):
        """
        Returns 2 strings with HTML code
        """
        # Show weird bond angles topology

        we = self.settings.Engine3D()

        b1, b2 = '', ''

        # b1:
        # 1. use 3D geom
        # 2. if not available, make 2D picture,
        # 3. if not available, make ASCII pseudographics
        # ...

        #b2 += 'Version: %s' % (self.NBO_version)  + web.brn
        if self.options:
            b2 += web.tag('NBO options:','strong')+web.brn
            b2 += self.options + web.brn
        if self.comments:
            b2 += self.comments + web.brn
        if self.OpenShell:
            b2 += web.tag('Alpha spin NBO interactions','strong') + web.brn
            b2 += self.setA.webData()
            b2 += web.tag('Beta spin NBO interactions','strong') + web.brn
            b2 += self.setB.webData()
        else:
            b2 += web.tag('NBO interactions','strong') + web.brn
            b2 += self.setAB.webData()

        log.debug('webData generated successfully')
        return b1, b2
#
#
#
#
#
if __name__ == "__main__":

    DebugLevel = logging.DEBUG
    logging.basicConfig(level=DebugLevel)

    from Settings import Settings
    Top.settings = Settings(FromConfigFile = True)

    f = NBO()
    f.file = sys.argv[1]
    f.parse()

    print f

"""
s_nbo_bond = rc['nbo-bond'].search(s)
if s_nbo_bond:
    at1, at2 = s_nbo_bond.group(1), s_nbo_bond.group(2)
    nbo_top.increaseOrder(at1, at2)
    nbo_top.increaseOrder(at2, at1)
"""
