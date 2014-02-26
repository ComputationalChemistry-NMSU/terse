import os,glob
import logging
import subprocess
import time
from Top import Top
log = logging.getLogger(__name__)

class IO(Top):
    def writeMOL(self, fname, geoms, topologies=None):
        """
        writes MOL file.
        Terse uses two file formats:
            1. MDL Molfile
                '+': Supports topology
            2. XYZ
                '+': Simple, easier to reuse
                '+': JMol supports extended format with vectors
            Normally, XYZ format is used. However, if there are no vibrational modes in the output file and NBO topology found,
        Molfile format can be used. (Not implemented)
        """

        file = self.settings.realPath(fname)
        if not geoms:
            log.warning('File %s: No coordinates to write!' % (file))
            return
        try:
            f = open(file,'w')
        except IOError:
            log.critical('Cannot open file "%s" for writing' % (file))
            return
        """
        e= -567.757342394   R(2,5)= 1.7
         OpenBabel07311213123D

          7  6  0  0  0  0  0  0  0  0999 V2000
           -1.2474    0.9235    0.0001 C   0  0  0  0  0  0  0  0  0  0  0  0
           -0.5334   -0.7125    0.0000 S   0  0  0  0  0  0  0  0  0  0  0  0
           -1.8521    1.0687   -0.8932 H   0  0  0  0  0  0  0  0  0  0  0  0
           -0.4079    1.6259   -0.0001 H   0  0  0  0  0  0  0  0  0  0  0  0
            1.1456   -0.4465    0.0000 N   0  0  0  0  0  0  0  0  0  0  0  0
            1.5606    0.6706    0.0001 O   0  0  0  0  0  0  0  0  0  0  0  0
           -1.8518    1.0688    0.8936 H   0  0  0  0  0  0  0  0  0  0  0  0
          1  7  1  0  0  0  0
          2  5  1  0  0  0  0
          2  1  1  0  0  0  0
          3  1  1  0  0  0  0
          4  1  1  0  0  0  0
          5  6  2  0  0  0  0
        M  END
        """

        """
        Remarks:
            # only 1 geometry supported
            # no comments supported
        """
        if len(geoms)>1:
            log.warning('Only one geometry is supported')
        geom = geoms[0]
        comment = geom.propsToString(ShowComment = True)
        sg = '%s\n%s\n\n' % (file,comment)

        nb = 0
        for a1 in topologies:
            nb += len(a1)
        sg += "%3s %3s  0  0  0  0  0  0  0  0999 V2000" % (len(geom),nb)
        for at in geom.coord:
            el,x,y,z = at.split()
            sg += "%10.4f%10.4f%10.4f %-2s   0  0  0  0  0  0  0  0  0  0  0  0\n" % (x,y,z,el)
        for a1 in topologies.keys():
            for a2 in topologies[a1].keys():
                sg += '%3s%3s  %1s  0  0  0  0\n' % (a1,a2,topologies[a1][a2])
        sg += ' M  END\n$$$$\n'

        f.write(sg)
        f.close()
        return



    def writePic(self, fname,xname='',yname='',y2name='',keys=None,x=None,y=None,ny2=0):
        file = self.settings.realPath(fname)
        try:
            f = open(file,'w')
        except IOError:
            log.critical('Cannot open file "%s" for writing' % (file))
            return

        log.debug('Starting gnuplot')
        try:
            proc = subprocess.Popen([self.settings.gnuplot,'-p'],
                            shell=True,
                            stdin=subprocess.PIPE,
                            stderr=subprocess.PIPE
                            )
        except:
            log.error('Cannot open gnuplot')
            return ''

        if not y:
            log.warning('Empty y')
            return ''

        if isinstance(y[0],(list,tuple)):
            ys = y # several curves
        else:
            ys = [y]

        if not x:
            x = range(1,len(ys[0])+1)

        # Make test if all y arrays have the same length
        # Strip each array at first encounter of ''
        min_len = len(x)
        for i in range(len(ys)):
            if len(ys[i]) < min_len:
                logging.warning('Y arrays have different length')
                min_len = len(ys[i])
            try:
                z = ys[i].index('')
                if z < min_len:
                    min_len = z
            except:
                pass

        if min_len<2:
            logging.debug('Only one point is given, skipping plot')
            return ''

        toGP = proc.stdin.write
        toGP("set term png\n")
        toGP("set xlabel '%s'\n" % (xname))
        toGP("set ylabel '%s'\n" % (yname))
        toGP("set output '%s'\n" % (file))

        n_left, n_right = len(ys)-ny2, ny2
        if not keys:
            keys = ('-',) * len(ys)

        pl  = "'-' with lp title '%s',"*n_left % tuple(keys[:n_left])
        pl += "'-' with lp axis x1y2 title '%s',"*n_right % tuple(keys[n_left:])

        #sys.exit()
        toGP("plot %s\n" % (pl[:-1]))
        for y in ys:
            for i in range(min_len):
                toGP('%s %s\n' % (x[i],y[i]))
            toGP('e\n')
        toGP("quit\n")

        log.debug(proc.stderr.read().rstrip())
        log.debug('Picture was saved to %s' % file)

        return self.settings.webPath(fname)


def all_readable(files):
    for f1 in files:
        if not is_readable(f1):
            return False
    return True

def is_readable(f):
    if os.access(f, os.R_OK):
        log.debug('File %s is readable' % (f))
        return True
    else:
        log.error('File %s is not readable' % (f))
        return False

def is_writable(f):
    if os.access(f, os.W_OK):
        log.debug('File %s is writable' % (f))
        return True
    else:
        log.error('File %s is not writable' % (f))
        return False

def cleanDir(d):
    files = glob.glob(d + '/*')
    try:
        for f in files:
            os.remove(f)
    except OSError:
        log.warning('Unable to clean up ' + d)
        return False
    log.debug(d + ' cleaned up')
    return True

def prepareDir(d):
    if os.path.exists(d):
        if not os.access(d,os.W_OK):
            log.critical(d + ' exists but not writable')
            return False
    else:
        log.warning(d + ' does not exist')
        try:
            os.mkdir(d)
            log.warning(d + ' created')
        except:
            log.critical(d + ' can not be created')
            return False
    return True

def cleanCube(d):
    files = glob.glob(d + '/*.cube')
    try:
        for f in files:
            os.remove(f)
    except OSError:
        log.warning('Unable to clean up cube files ' + d)
        return False
    log.debug(d + ' cleaned up')
    return True

#def backupdir(d):
#    if os.path.exists(d):
#        if not os.access(d,os.W_OK):
#            log.critical(d + ' exists but not writable')
#            return False
#    else:
#        log.warning(d + ' does not exist')
#        try:
#            os.mkdir(d)
#            log.warning(d + ' created')
#        except:
#            log.critical(d + ' can not be created')
#            return False
#    return True

def RunJmol(JmolAbsPath,script):
    # Create temporary file
    tmp_fname = '/tmp/terse.tmp' # Make a better filename!
    FI = open(tmp_fname,'w')
    # Write script in that file
    FI.write(script)
    FI.close()

    runjmol = '/bin/sh %s/Jmol.sh -s %s -n' % (JmolAbsPath,tmp_fname)
    # Run JMol
    t1 = time.time()
    log.debug('Trying to run command: ' + runjmol )
    subprocess.call(runjmol.split())
    t2 = time.time()
    log.debug('Done in %.1f s' % (t2-t1))
