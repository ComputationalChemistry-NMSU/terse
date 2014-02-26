import os, re, sys, time
from argparse import ArgumentParser,RawTextHelpFormatter
import logging
from Engine3D import JMol,JSMol
from Top import Top
from datetime import datetime
log = logging.getLogger(__name__)

class Settings(Top):
    """
    Operates with settings. Three levels of settings are supported:
        hard-coded, from configuration file, and from command line.
        Settings in each level can overwrite data in previous ones.
    """
    def __init__(self, FromConfigFile = True):
        self.OutputFolder = os.environ['HOME']+'/Sites/'
        #self.BackupFolder = os.environ['HOME']+'/Sites/terse-backup/'
        self.tersepic = 'terse-pics/'
        self.configFile = os.environ['HOME']+'/.terse.rc'
        self.tersehtml = 'terse.html'
        self.JmolFolder = './Jmol/'

        self.debug = False
        self.usage = False

        self.suffix = time.strftime('%y-%m-%d--%H-%M-%S')
        self.timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")

        self.EnergyUnits = 'kJ/mol'
        self.EnergyFactor = 2625.5
        self.inbo_threshold = 10.0
        self.connectivityMode = 0
        self.FullGeomInfo = False
        self.textirc = False
        self.ircgrad = 0
        self.full = False

        self.counter = 1
        self.subcounter = 0

        self.npoints_cube = '0'
        self.save_cube = False
        self.color_mo_plus = 'red'
        self.color_mo_minus = 'blue'

        self.gnuplot = 'gnuplot'
        self.cubegen = 'cubegen'
        self.formchk = 'formchk'
        self.useJVXL = True
        self.Engine3D = JSMol
        self.JSMolLocation = "http://comp.chem.mu.edu"

        self.JmolWinX, self.JmolWinY = 800, 600
        self.JavaOptions = """vector ON; vector SCALE 3;\\
        set animationFPS 10;\\
        set measurementUnits pm;\\
        set measureAllModels ON;\\
        wireframe 20; spacefill 40;\\
        """
        if FromConfigFile:
            self.readConfig()


    def setArgVal(self, line):
        """
        Imports attr=value to settings. It will be accessible as settings.attr
        """

        s = re.search('\s*(\S+)\s*=\s*(.*)',line)
        if s:
            attr = s.group(1)
            value = s.group(2)
            setattr(self, attr, value)


    def readConfig(self):
        """
        Read configuration file
        """

        try:
            f = open(self.configFile,'r')
            for line in f:
                l = line.strip()
                if '#' in l:
                    l = line.split('#')[0] # Strip comments
                self.setArgVal(l)
            f.close()
            #self.float()
            log.debug('Configuration file %s was successfully loaded' % (self.configFile))
        except IOError:
            log.warning("Cannot open config file " + self.configFile)


    def parseCommandLine(self, args):
        """
        Parse command line parameters
        """

        descr = """
        terse.py - Helps to perform express visual analysis of output files of
                   electronic structure calculations (mostly, Gaussian).
                   The main idea of this script is to collect results of multiple calculations
                   in one HTML file. For each calculation, short text description of each step will be given,
                   and most important geometries will be shown in 3D mode using Jmol inside the web page.
        Features:
                   Visualization of several files on the same web page
                   Thorough extraction of chemical data
                   Extensive support of Gaussian package
                   Basic support of US-Gamess, Firefly packages
                   Gzipped files supported
                   Stand-alone program, requires minimum dependencies
        Requirements:
                   Python (also need argparse 'pip install argparse')
                   OpenBabel (must install with python bindings and png)
                   Gnuplot (optional, used for convergence/Scan/IRC plot generation)
                   Web browser supporting Java Machine (to view resulting web page)
                   Jmol (to show molecules in 3D mode on the web page)
                   JSMol (to show molecules in 3D mode on the web page using javascript)
        Author:
                   Marat Talipov, marat.talipov@marquette.edu
        """
        sp = sys.argv[0]
        self.selfPath = sp[:sp.rfind('/')+1]
        ar = sys.argv[1:]
        parser = ArgumentParser(descr, formatter_class=RawTextHelpFormatter)
        parser.add_argument('--connectivityMode', action='store_true', help='Show set of internal coordinates')
        parser.add_argument('--debug', action='store_true', help='Debug mode')
        parser.add_argument('--usage', action='store_true', help='Shows small statistics on CPU usage')
        parser.add_argument('--full', action='store_true', help='Show more detailed information')
        #parser.add_argument('irc', help='Force terse.pl to consider two files as the part of the same IRC calculation')
        parser.add_argument('--inbo', help='Show interacting NBO orbitals; specially arranged Gaussian calculation needed,\nneeds two keys, "l" and "c"(optional key "t").\nUsage: terse.py --inbo l=LOGFILE --inbo c=CHECKPOINTFILE\nOptional usage: --inbo t=NBOENERGYTHRESHHOLD(default is 10 kcal/mol)',action='append',default=[])
        parser.add_argument('--jvxl', help='Show JVXL isosurface, needs two keys, "j" and "x"',action='append',default=[])
        parser.add_argument('--isosurface', help='Show isosurface from Gaussian .chk file',action='append',default=[])
        parser.add_argument('--settings', help='Redefine settings',action='append',default=[])
        #parser.add_argument('uv', help='Show interacting NBO orbitals')
        parser.add_argument('--local', help='Write terse pages to local folder in Sites. Useful for saving\nterse pages to some local archive.\nUsage: terse.py --local=$HOME/Sites/PATH_TO_ARCHIVE_DIR',action='store')
        parser.add_argument('--spin', help='Show spin density',action='store_true')
        parser.add_argument('--homo', help='Show HOMO',action='store_true')
        parser.add_argument('--lumo', help='Show LUMO',action='store_true')
        parser.add_argument('--mos', help='Show selected MOs',action='store')
        parser.add_argument('--amos', help='Show selected alpha-MOs',action='store')
        parser.add_argument('--bmos', help='Show selected beta-MOs',action='store')
        parser.add_argument('input', nargs='*',help='Files to parse')
        #parser.add_argument('--rmcube', help='Remove cube files from DIR after JVXL created', action='store_true')
        #parser.add_argument('--backup', help='Backup Mode: Create web page in backup directory for later use',action='store')
        args = parser.parse_args(ar)
        self.opts_cl = vars(args)

        if self.opts_cl['connectivityMode']:
            self.connectivityMode = True
        if self.opts_cl['full']:
            self.full = True
        if self.opts_cl['debug']:
            self.debug = True
        if self.opts_cl['usage']:
            self.usage = True
        if self.opts_cl['local']:
            self.OutputFolder = self.opts_cl['local']
        #if self.opts_cl['backup']:
        #    self.OutputFolder = self.BackupFolder

        for opt in self.opts_cl['settings']:
            self.setArgVal(opt)

        if self.debug:
            self.exc_type = None
        else:
            self.exc_type = Exception

        #self.float()

        files = []
        isosurf = False
        if self.opts_cl['spin']:
            isosurf = True
            for f in self.opts_cl['input']:
                files.append(('iso',{'type':'spin','c':f,'iv':0.001}))
        if self.opts_cl['homo']:
            isosurf = True
            for f in self.opts_cl['input']:
                files.append(('iso',{'type':'mo=homo','c':f,'iv':0.03}))
        if self.opts_cl['lumo']:
            isosurf = True
            for f in self.opts_cl['input']:
                files.append(('iso',{'type':'mo=lumo','c':f,'iv':0.03}))
        if self.opts_cl['mos']:
            isosurf = True
            mos = self.opts_cl['mos'].split(',')
            mos2 = []
            for mo in mos:
                if '-' in mo:
                    range_start,range_end = mo.split('-')
                    for i_mo in range(int(range_start),int(range_end)+1):
                        mos2.append(str(i_mo))
                else:
                    mos2.append(mo)
            for f in self.opts_cl['input']:
                for mo in mos2:
                    files.append(('iso',{'type':'mo='+mo,'c':f,'iv':0.03}))
        if self.opts_cl['amos']:
            isosurf = True
            mos = self.opts_cl['amos'].split(',')
            mos2 = []
            for mo in mos:
                if '-' in mo:
                    range_start,range_end = mo.split('-')
                    for i_mo in range(int(range_start),int(range_end)+1):
                        mos2.append(str(i_mo))
                else:
                    mos2.append(mo)
            for f in self.opts_cl['input']:
                for mo in mos2:
                    files.append(('iso',{'type':'amo='+mo,'c':f,'iv':0.03}))
        if self.opts_cl['bmos']:
            isosurf = True
            mos = self.opts_cl['bmos'].split(',')
            mos2 = []
            for mo in mos:
                if '-' in mo:
                    range_start,range_end = mo.split('-')
                    for i_mo in range(int(range_start),int(range_end)+1):
                        mos2.append(str(i_mo))
                else:
                    mos2.append(mo)
            for f in self.opts_cl['input']:
                for mo in mos2:
                    files.append(('iso',{'type':'bmo='+mo,'c':f,'iv':0.03}))
        if not isosurf:
            for f in self.opts_cl['input']:
                files.append(('file',f))


            # isosurface
            iso_files = parse_dict(Dict=self.opts_cl['isosurface'],DictName='iso',LeadingSymbol='c')
            files.extend(iso_files)

            # inbo
            inbo_files = parse_dict(Dict=self.opts_cl['inbo'],DictName='inbo',LeadingSymbol='l')
            files.extend(inbo_files)

            # JVXL
            jvxl_files = parse_dict(Dict=self.opts_cl['jvxl'],DictName='jvxl',LeadingSymbol='j')
            files.extend(jvxl_files)

        return files


    def float(self):
        for a,v in self.__dict__.iteritems():
            try:
                fv = float(v)
                setattr(self,a,fv)
            except:
                pass


    def realPath(self, fname):
        s = '%s/%s/%s--%i-%i%s' % (self.OutputFolder, self.tersepic, self.suffix, self.counter, self.subcounter, fname)
        return s


    def webPath(self, fname):
        s = './%s/%s--%i-%i%s' % (self.tersepic, self.suffix, self.counter, self.subcounter, fname)
        return s


def parse_dict(Dict,DictName,LeadingSymbol):
    """
    # this comment relates more to iNBO than to this function, and doe not make much sense
    Several kinds of syntax will be available for dictionaries (on example of NBO):
        1. Simplified, only log file is provided: --inbo a.log
            1.1. Assume that path to the .chk file can be found in the .log file
            1.2. If this file is not found, assume that the .chk file has the same basename as .log file
            1.3. Fail
           As we might need to parse .log file to get the name .chk file name,
           preliminary test for file existence will be incomplete
        2. Normal, like --inbo c=a.chk --inbo l=a.log
        3. Extended, like --inbo c1=a.chk --inbo l1=a.log --inbo c2=b.chk --inbo l2=b.log
        4. Another flavor of extended format: --inbo l1=a.log --inbo l2=b.log
            In this case, .chk file name will be guessed as in 1., but many iNBO results can be shown in one web page
    """
    implicit_counter = 0
    files = []
    jobs = {}
    for arg in Dict:
        # Separate keys from values
        ssplit = arg.split('=',1)
        if len(ssplit)==1:
            # Deal with simplified input 1.
            key,value = LeadingSymbol,ssplit[0]
        else:
            key,value = ssplit
        if re.search('^'+LeadingSymbol,key):
            implicit_counter += 1
        # If job index is not provided, use implicit counter
        if not re.search('\d+',key):
            key += str(implicit_counter)
        # Split keys by job numbers
        k,i = re.search('^(\D+)(\d+)$',key).groups()
        i = int(i)
        if not i in jobs:
            jobs[i] = {}
        jobs[i][k]=value
    for job in sorted(jobs):
        files.append((DictName,jobs[job]))
    return files


if __name__ == "__main__":
    print "Test output"
    print "\n===Hard-coded settings:==="
    s = Settings(FromConfigFile = False)
    print s
    print "\n===Settings updated from config file (%s)===" % (s.configFile)
    s.readConfig()
    print s
    print "\n===Settings updated from the command line==="
    s.parseCommandLine(sys.argv)
    print s
