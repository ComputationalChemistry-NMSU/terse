#! /usr/bin/env python

import sys
from Settings import Settings
from HTML import HTML
import logging
import Tools.web as web
from Assigner import ParserAssigner
import Tools.IO as IO
from Top import Top

#DONE read/write E and gradients from/to .xyz file; make plots if E/dE available
#DONE rearrange geometry optimization buttons on the web page
#DONE add UI element to play geometries faster
#DONE recognize forward/reverse directions of IRC, assign negative sign to the reverse one
#DONE recognize Energy: record in .xyz comments
#DONE clean up b2 section of .xyz file when big irc file is shown
#DONE clean terse-pics folder before writing
#DONE add support for conversion to kcal/mol in .xyz comments
#DONE Write supplementary IRC  classes
#DONE XYZ: make it to recognize synonims for e and grad
#DONE Write supplementary Geometry classes (+Gau)
#DONE Remove unnecessary solvation n/a
#DONE Put IRC direction in title
#DONE Geometry-specific comments should be stored in Geom objects and printed from Geom.comment
#DONE In Gaussian.py and ElectronicStructure.py, organize scan using object Scan()
#DONE show maxima/minima on scans
#DONE Gaussian.py: IRC gradients: used Delta-E instead
#DONE Gaussian.py: IRC gradients: search for minima on smoothed curve
#DONE check showPic for number of points
#DONE add charges support
#DONE stability support
#DONE Charges: Add charges of hydrocarbon H atoms to heavy atoms
#DONE add support for gs2 and dvv IRC options
#DONE Show largest amplitudes in Gau
#DONE Figure out if we can skip parsing of some big useless blocks in .log file
#DONE add .chk isosurfaces module
#DONE work with gaussian checkpoint files (in the same manner as .log files)
#DONE parse .nbout files
#DONE Charges: figure out the best way of organizing UI for charges
#DONE show NBO interactions
#DONE Unfold menu with list of geoms to buttons
#DONE Support JSmol
#DONE Resize Jmol window

# Top priority
#TODO Add backup functionality
#TODO Support JVXL format
#TODO show TDDFT orbitals involved in excitation
#TODO Write a python script to parallelize cubegen
#TODO work with gzipped files
#TODO Make html and gp files as templates

# To do next
#TODO connectivity mode

# Reimplement functionality:

# Nice featrues to add:
#TODO what are Natural Transition Orbitals?
#TODO attach NRT module
#TODO Scan recursively and recreate the folder hierarchy
#TODO add cclib support
#TODO add AIM support
#TODO recognize file type by content
#TODO Support 2D scan plots
#TODO support mp2 and semiempirics calculations
#TODO Show electronic state of the wavefunction if it has any symmetry
#TODO Make second run for terse to parse .xyz files in terse-pics to merge scans/ircs
#TODO User interface: use buttons; they don't change their state!
#TODO fchkgaussian: Instead of looking for predefined densities (SCF, MP2, etc), parse them!
#TODO IRC: add key to sort geometris!
#TODO Think about using /tmp dir and clean up procedure
#TODO Show energies in optimization convergence plot
#TODO Show molecule in 2D if NBO analysis is done
#TODO Export text information
#TODO Show vectors
#TODO NBO results: show correct topology
#TODO installer
#TODO self-doctor

# Bugs
# [ ] Jmol does not show array of text labels

# Postponed
#XXX Show IRC as text in Jmol window
#       Problem: cannot echo variable in jmol; need to subscribe to jmol-users and ask about that
#XXX Find the way to set Jmol interactive elements from inside html code

# Rejected
#XXX Apply bond orders manually if NBO_topology present
#       What's the use?
#XXX Gaussian Merge IRC files - For now, I don't think it is really a good idea.
#       Instead, .xyz files produced by terse.py should be merged (they have all neccessary information like e, x, and grad in comments)
#       Advantage of this approach is ESS independence
#XXX Gaussian: Figure out why post_hf lot is determined incorrectly and energies do not show up
#       For now this functionality does not look necessary, as we rarely use MP2 and CI, and there exist better programs for CC and MR
#XXX color logging:
#       Gives nothing to functionality but might add issues with OS compatibility
#XXX T1 diagnostics
#       Gaussian does not show t1 diagnostic by default, and it can not be activated in CBS-QB3
#       procedure, so for now showing t1 diagnostics would not be very helpful
#XXX write topology to .mol file
#       Using different file formats is inconvinient, and implementing topologies does not worth that mess.

#debug = 'DEBUG'

settings = Settings(FromConfigFile = True)
Top.settings = settings
files = settings.parseCommandLine(sys.argv[1:])


if settings.debug:
    debug = 'DEBUG'
else:
    debug = 'INFO'

log = logging.getLogger('terse.py')
DebugLevel = getattr(logging,debug)
lf = '[%(levelname)s: %(funcName)s at %(filename)s +%(lineno)s] %(message)s'
logging.basicConfig(format=lf ,level=DebugLevel)

absolute_tersepic = settings.OutputFolder + '/' + settings.tersepic

if not IO.prepareDir(settings.OutputFolder):
    sys.exit()
if not IO.prepareDir(absolute_tersepic):
    sys.exit()

IO.cleanDir(absolute_tersepic)

WebPage = HTML()
WebPage.readTemplate()

for fl in files:
    log.debug('Opening ' + str(fl))

    if fl[0] == 'file':
        if not IO.all_readable(fl[1:]):
            continue
        f = ParserAssigner().typeByExt(fl)
    else:
        f = ParserAssigner().typeByCommandLine(fl)
    f.file = fl[1]

    try:
        f.parse()
        f.postprocess()
        b1, b2 = f.webData()
    except settings.exc_type, e:
        log.error('Parsing %s failed!' % (str(fl)))
        continue
    wb1 = WebPage.addLeftDiv(b1)
    wb2 = WebPage.addRightDiv(b2)
    WebPage.addDivRowWrapper(str(f.file)+web.brn+wb1,wb2)

    if settings.usage:
        f.usage()

    settings.counter += 1
    settings.subcounter = 0

# Remove cube files from terse-pics
# IO.cleanCube(absolute_tersepic)
WebPage.finalize()
WebPage.write()
