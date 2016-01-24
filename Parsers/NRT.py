if __name__ == "__main__":
    import sys,os
    selfname = sys.argv[0]
    full_path = os.path.abspath(selfname)[:]
    last_slash = full_path.rfind('/')
    dirpath = full_path[:last_slash] + '/..'
    print "Append to PYTHONPATH: %s" % (dirpath)
    sys.path.append(dirpath)

import copy, string
import math
import numpy
import time,re,logging
from math import sqrt
from Tools import web
from Tools.BetterFile import BetterFile
from Top import Top
from Containers import Topology, AtomicProps
log = logging.getLogger(__name__)

class bondM(Top):
    """
    This class represents a resonance structure
    """
    def __init__(self, nA, symbols, data, name=''):
        self.symbols = symbols
        self.data = data
        self.name = name

        if self.symbols == []:
            for i in range(nA):
                self.symbols.append("")

        if self.data == []:
            for i in range(nA):
                tmp = []
                for j in range(nA):
                  tmp.append(0)
                self.data.append(tmp)
        self.wg = 0.0
    """
    *
    """
    def __getitem__(self,key):
        return self.data[key]
    """
    *
    """
    def __lt__(self, other):
        return self.wg < other.wg
    """
    *
    """
    def __eq__(self, other, CheckSymbols = True):
        """
        :param CheckSymbols: If selected, additional check for chemical elements symbols matching will be performed
        """
        if CheckSymbols:
            match = True
            for i in range(len(self.symbols)):
                    if (self.symbols[i] != other.symbols[i]) \
                    and (self.symbols[i].upper() != 'X') \
                    and (other.symbols[i].upper() != 'X'):
                        match = False
                        break
            if not match:
                return False

        i = 0
        for i in range(len(self.data)):
            for j in range(len(self.data[i])):
                if self.data[i][j] != other.data[i][j]:
                    return False

        return True
    """
    *
    """
    def __sub__(self,other, CheckSymbols = False):
        diff = copy.deepcopy(self)
        """
        Subtracts two connectivity matrices

        :param CheckSymbols: If selected, additional check for chemical elements symbols matching will be performed
        :return: a new matrix with difference
        :rtype: an object of class bondM
        """
        if CheckSymbols and (self.symbols != other.symbols):
            return False
        for i in range(len(self.data)):
            for j in range(len(self.data[i])):
                diff[i][j] = self[i][j] - other[i][j]
        return diff
    """
    *
    """
    def __add__(self,other, CheckSymbols = False):
        sm = copy.deepcopy(self)
        """
        Adds two connectivity matrices

        :param CheckSymbols: If selected, additional check for chemical elements symbols matching will be performed
        :return: a new matrix with sums
        :rtype: an object of class bondM
        """
        if CheckSymbols and (self.symbols != other.symbols):
            return False
        for i in range(len(self.data)):
            for j in range(len(self.data[i])):
                sm[i][j] = self[i][j] + other[i][j]
        return sm

    """
    *
    """
    def __str__(self):
        return self.as_matrix()
    """
    *
    """
    def as_matrix(self):
        """
        :returns: a string with resonance structure in matrix format
        :rtype: str
        """
        nA = len(self.data)
        tStr = "      "

        for i in range(len(self.data)):
            tStr += " % 3s" % (self.symbols[i])
        tStr += "\n"

        tStr += "      "
        for i in range(len(self.data)):
            tStr += " % 3i" % (i+1)
        tStr += "\n"

        tStr += "       "

        for i in range(len(self.data)):
            tStr += " ---"
        tStr += "\n"

        for i in range(len(self.data)):
            tStr += "%s% 3i |  " % (self.symbols[i], i+1)
            for b in self.data[i]:
                if b == 0:
                    tStr += " .  "
                else:
                    tStr += " %1i  " % (b)
            tStr += "\n"
        return tStr
    """
    *
    """
    def offDiag(self):
        """
        :returns: only off-diagonal elements thus removing information about lone pairs
        :rtype: Instance of class bondM
        """
        od = copy.deepcopy(self)
        for i in range(len(od.data)):
            od.data[i][i] = 0
        return od
    """
    *
    """
    def offDiagEQ(self, other):

        if self.symbols != other.symbols:
            return False

        i = 0
        for i in range(len(self.data)):
            for j in range(len(self.data)):
                if i == j:
                    continue
                if self.data[i][j] != other[i][j]:
                    return False

        return True
    """
    *
    """
    def subset(self, subset):
        """
        :param subset: a list of indices of selected atoms
        :returns: a submatrix, which is a matrix including only selected atoms
        :rtype: instance of class bondM
        """
        nA = len(self.data)

        # curiously enough, we need to explicitly provide optional empty data, otherwise it will copy the data of the
        # current instance!
        smallM = bondM(len(subset),symbols = [], data =[])

        for i in range(len(subset)):
            smallM.symbols[i] = self.symbols[subset[i]-1]
            for j in range(len(subset)):
                smallM[i][j] = self.data[subset[i]-1][subset[j]-1]

        return smallM
    """
    *
    """
    def as_lines(self,wrap=False):
        """
        Return a bond matrix in format compatible with $CHOOSE, $NRTSTR groups
        """
        mt = self.data
        nA = len(self.data)
        s = "  STR !"
        if self.name:
            s += " name="+self.name+','
        s+= " weight="+str(self.wg)+','
        s+= " symbols="+self.writeSymbols()
        s += "\n   LONE"
        for i in range(nA):
            if mt[i][i] > 0:
                s = s + " %i %i" % (i+1,mt[i][i])
        s = s + " END\n   BOND "
        counter = 0
        for i in range(nA):
            for j in range(i+1,nA):
                if mt[i][j] == 1:
                    s = s + " S %i %i" % (i+1,j+1)
                    counter += 1
                    if wrap and (counter % 10 == 0):
                        s = s+ "\n        "
                if mt[i][j] == 2:
                    s = s + " D %i %i" % (i+1,j+1)
                    counter += 1
                    if wrap and (counter % 10 == 0):
                        s = s+ "\n        "
                if mt[i][j] == 3:
                    s = s + " T %i %i" % (i+1,j+1)
                    counter += 1
                    if wrap and (counter % 10 == 0):
                        s = s+ "\n        "
        s = s + " END\n  END\n"

        return s
    """
    *
    """
    def as_choose(self,wrap=False):
        """
        Return a bond matrix in format compatible with $CHOOSE, $NRTSTR groups
        """
        mt = self.data
        nA = len(self.data)
        s = "   LONE"
        for i in range(nA):
            if mt[i][i] > 0:
                s = s + " %i %i" % (i+1,mt[i][i])
        s = s + " END\n   BOND "
        counter = 0
        for i in range(nA):
            for j in range(i+1,nA):
                if mt[i][j] == 1:
                    s = s + " S %i %i" % (i+1,j+1)
                    counter += 1
                    if wrap and (counter % 10 == 0):
                        s = s+ "\n        "
                if mt[i][j] == 2:
                    s = s + " D %i %i" % (i+1,j+1)
                    counter += 1
                    if wrap and (counter % 10 == 0):
                        s = s+ "\n        "
                if mt[i][j] == 3:
                    s = s + " T %i %i" % (i+1,j+1)
                    counter += 1
                    if wrap and (counter % 10 == 0):
                        s = s+ "\n        "
        s = s + " END\n"

        return s
    """
    *
    """
    def applyMatrix(self, matrix, row=0 ,col=0):
        """
        Implements elements of a matrix into self. See source for detailed example
        """
        """
        A.data = X X X X X, B = Y Y, row=1,col=1                        A.data  = X X X X X
                 X X X X X      Y Y                A.applyMatrix(B,1,1) =>        X Y Y X X
                 X X X X X                                                        X Y Y X X
                 X X X X X                                                        X X X X X
                 X X X X X                                                        X X X X X
        """
        nX = len(matrix)
        nY = len(matrix[0])
        for i in range(nX):
            for j in range(nY):
                self.data[row+i][col+j] = matrix[i][j]
    """
    *
    """
    def applySubset(self, other, subset):
        """
        Updates connectivity matrix for atoms in subset with connectivity matrix given in object of class bondM
        """
        for i in range(len(subset)):
            for j in range(len(subset)):
                self.data[subset[i]-1][subset[j]-1] = other.data[i][j]
    """
    *
    """
    def writeSymbols(self):
        """
        converts the list of chemical symbols into string
        """
        s = ''
        for Symbol in self.symbols:
            if s:
                s += ' '
            if Symbol == '':
                s += '-'
            else:
                s += Symbol
        return s
    """
    *
    """
    def applyStringSymbols(self,s):
        """
        converts the a string with chemical symbols into list and applies it to the object
        """
        syms = s.split(' ')
        for i in range(len(syms)):
            if syms[i]=='-':
                syms[i]=''
        self.symbols = syms
    """
    *
    """
    def diffColor(self,other):
        """
        Compares self and other matrices.
        The result is a string representing a difference matrix. The elements that differ are highlighted.
        """
        nA = len(self.data)
        tStr = "      "

        for i in range(len(self.data)):
            tStr += " % 3s" % (self.symbols[i])
        tStr += "\n"

        tStr += "      "
        for i in range(len(self.data)):
            tStr += " % 3i" % (i+1)
        tStr += "\n"

        tStr += "       "

        for i in range(len(self.data)):
            tStr += " ---"
        tStr += "\n"

        for i in range(len(self.data)):
            tStr += "%s% 3i |  " % (self.symbols[i], i+1)
            for j in range(len(self.data[i])):
                if self.data[i][j] != other[i][j]:
                    tStr += '\033[1;31m'

                if self.data[i][j] == 0:
                    tStr += " .  "
                else:
                    tStr += " %1i  " % (self.data[i][j])

                if self.data[i][j] != other[i][j]:
                    tStr += '\033[0;00m'

            tStr += "\n"
        return tStr
    """
    *
    """
    def pic(self,filename,picformat='svg'):
        """
        Generates a graphical file with 2D-representation of the resonance structure
        """
        try:
            import openbabel as ob
        except:
            print "Cannot import openbabel"
            return

        #ValEl = {'H':1, 'B':3,'C':4,'N':5,'O':6,'F':7,'S':6}
        #ValEl = {'1':1, '5':3,'6':4,'7':5,'8':6,'9':7,'16':6}
        # Import Element Numbers
        ati = []
        Sym2Num = ob.OBElementTable()
        for a in self.symbols:
            ElNum = Sym2Num.GetAtomicNum(a)
            ati.append(ElNum)

        # Import connections
        conn = self.data

        mol = ob.OBMol()

        # Create atoms
        for a in ati:
            at = ob.OBAtom()
            at.SetAtomicNum(a)
            mol.AddAtom(at)

        # Create connections
        val = []
        total_LP = 0
        for i in range(len(conn)):
            total_LP += conn[i][i]

        for i in range(len(conn)):
            val.append(conn[i][i] * 2)
            for j in range(i):
                if conn[i][j]==0:
                    continue
                val[i] += conn[i][j]
                val[j] += conn[i][j]
                atA = mol.GetAtomById(i)
                atB = mol.GetAtomById(j)

                b = ob.OBBond()
                b.SetBegin(atA)
                b.SetEnd(atB)
                b.SetBO(int(conn[i][j]))
                mol.AddBond(b)
        for i in range(len(conn)):
            atA = mol.GetAtomById(i)
            atAN = atA.GetAtomicNum()
            FormValEl = CountValenceEl(atAN)
            #if total_LP == 0:
            #    if atAN == 1:
            #        FullShell = 2
            #    else:
            #        FullShell = 8
            #    FormCharge = FormValEl + int(val[i]) - FullShell
            #else:
            FormCharge = int(FormValEl - val[i])
            #print "atAN, FormValEl, val[i], FullShell"
            #print atAN, FormValEl, val[i], FullShell
            #FormCharge = FormCharge % 2
            atA.SetFormalCharge(FormCharge)

        # Export file
        mol.DeleteNonPolarHydrogens()
        conv = ob.OBConversion()
        conv.SetOutFormat(picformat)
        conv.AddOption('C')
        conv.WriteFile(mol,filename)

        #print val
        #c2 = ob.OBConversion()
        #c2.SetOutFormat('mol2')
        #print c2.WriteString(mol)

    def CountValenceEl(x):
        """
        Returns a number of valence electrons among the x electrons.
        """
        x = int(x)
        nmax = int(sqrt(x/2))
        val = x
        for i in range(nmax+1):
            n = 2*i*i
            if n < val:
                val -= n
        return val


class NRT(Top):
    """
    This class represents a collection of resonance structures.
    """
    def __init__(self):
        self.FI = None
        self.options = ''
        self.NBO_version = ''
        self.structures = []
        self.symbols = []

    def parse(self):
        if self.FI:
            FI = self.FI
        else:
            FI = BetterFile(self.file)

    def read(self, fInp='',fType=''):
        if fType=='matrix':
            self.read_matrix(fInp)
        elif fType=='lines':
            self.read_lines(fInp)
        elif not self.read_matrix(fInp):
            self.read_lines(fInp)

    def __str__(self):
        return self.as_lines()

    def __len__(self):
        return len(self.structures)

    def __getitem__(self,key):
        return self.structures[key]

    def write(self,file):
        f = open(file,'w')
        f.write(str(self))
        f.close()

    def sortByWg(self):
        """
        Sorts resonance structures by weight in descending order
        """
        self.structures = sorted(self.structures, key = lambda k: k.wg, reverse = True)

    def as_lines(self):
        """
        Returns a string with resonance structures written as in the end of .nbout file
        """
        s = " $NRTSTR\n"
        if self.symbols:
            s = s + " !SYMBOLS " + str(self.symbols) + "\n"
        for rs in self.structures:
            s = s + rs.as_lines()
        return s + " $END\n"
    """
    *
    """
    def totalWg(self):
        """
        Returns sum of weights of resonance structures
        """
        sm = 0
        for mtrx in self.structures:
            sm += mtrx.wg
        return sm

    """
    *
    """
    def byName(self,name):
        """
        Returns a resonance structure (instance of class bondM) with a given name
        """
        for rs in self.structures:
            if rs.name == name:
                return rs
    """
    *
    """
    def patternsOfSubset(self,subset,OffDiag = False):
        """
        Returns connectivity patterns for a given subset of atoms.
        Weights of these patterns are calculated.
        """
        Patterns = SetOfResStr()
        for i_mtrx in range(len(self.structures)):
            mtrx = self.structures[i_mtrx]
            if OffDiag:
                currMat = mtrx.subset(subset).offDiag()
            else:
                currMat = mtrx.subset(subset)
            if currMat in Patterns.structures:
                i = Patterns.structures.index(currMat)
                Patterns.structures[i].wg += mtrx.wg
                Patterns.structures[i].indices.append(i_mtrx)
            else:
                Patterns.structures.append(currMat)
                Patterns.structures[-1].wg = mtrx.wg
                Patterns.structures[-1].indices = [i_mtrx,]
        """
        for mtrx in self.structures:
            if OffDiag:
                currMat = mtrx.subset(subset).offDiag()
            else:
                currMat = mtrx.subset(subset)
            if currMat in Patterns.structures:
                i = Patterns.structures.index(currMat)
                Patterns.structures[i].wg += mtrx.wg
            else:
                Patterns.structures.append(currMat)
                Patterns.structures[-1].wg = mtrx.wg
        """
        return Patterns
    """
    *
    """
    def getWeights(self,NBO_RS):
        """
        Updates weights of reference structures, if they are found in NBO_RS
        :param NBO_RS: an object of class SetOfResStr, where resonance structures will be looked for.
        """
        for mtrx in self.structures:
            mtrx.wg = 0
            if mtrx in NBO_RS.structures:
                iPat = NBO_RS.structures.index(mtrx)
                mtrx.wg = NBO_RS.structures[iPat].wg
                mtrx.indices = NBO_RS.structures[iPat].indices
    """
    *
    """
    def offDiag(self):
        """
        Returns an instance of SetOfResStr class with zeroed diagonal elements of resonance structure matrices
        (in other words, with lone pairs removed)
        """
        od = copy.deepcopy(self)
        for i in range(len(self.structures)):
            od.structures[i] = self.structures[i].offDiag()
        return od
    """
    *
    """
    def read_matrix(self,fInp = ''):
        """
        Reading the resonance structs. This can handle split TOPO matrices determine the number of atoms
        """
        if fInp:
            try:
                inp = open(fInp,'r')
            except:
                print '[Warning]: cannot open %s' % (fInp)
                return
        else:
           inp = sys.stdin

        s = inp.readline()
        while s:
            if "Atom distance matrix:" in s:
                break
            s = inp.readline()

        inp.readline()
        inp.readline()
        inp.readline()

        nAtoms = 0
        s = inp.readline()
        while s:
            # atom numbers go like "1." so they must convert into a float, if not then we are done
            try:
                float(s.split()[0])
            except:
                break
            nAtoms += 1
            s = inp.readline()
        # read the main structure
        main = bondM(nAtoms,[],[])

        s = inp.readline()
        while s:
            if "TOPO matrix for" in s:
                break
            s = inp.readline()
        inp.readline()

        atomsPerLine = len(inp.readline().split()) -1

        nPasses = int(math.ceil(float(nAtoms)/atomsPerLine))

        inp.readline()

        for aPass in range(nPasses):
            for i in range(nAtoms):
                L = inp.readline().split()
                main.symbols[i]=L[1]
                for j in range(len(L)-2):
                    main[i][aPass*atomsPerLine+j] = int(L[j+2])
            if aPass < nPasses - 1:
                inp.readline()
                inp.readline()
                inp.readline()

        s = inp.readline()
        while s:
            if "---------------------------" in s:
                break
            s = inp.readline()

        # here comes the parsing of the other structs

        # the main first , just the %
        line = inp.readline()
        try:
            main.wg = float(line[10:17])
        except:
            return False

        struct_lns = []

        line = inp.readline()
        while line:
            if "---------------------------" in line:
                break
            if line[4] == " ":
                struct_lns[-1] += line.strip("\n")[18:]
            else:
                struct_lns.append(line.strip("\n"))
            line = inp.readline()

        allStructs = []
        allStructs.append(main)
        for tStr in struct_lns:
            tmpM = copy.deepcopy(main)
            tmpM.wg = float(tStr[10:17])

            #print tStr
            dontInclude = False
            for mod in tStr[18:].split(','):
                mod = mod.strip()
                if len(mod.split()) == 0:
                    dontInclude = True
                    break
                increment = 0
                if mod[0] == "(":
                    increment -= 1
                    aList = mod.strip("()").split("-")
                else:
                    increment += 1
                    aList = mod.split("-")
                aL2 = []
                for aL in aList:
                    aL2.append(int(aL.strip(string.letters+" "))-1)

                if len(aL2) == 2:
                    tmpM[aL2[0]][aL2[1]] += increment
                    tmpM[aL2[1]][aL2[0]] += increment
                elif len(aL2) == 1:
                    tmpM[aL2[0]][aL2[0]] += increment

            if not dontInclude:
                allStructs.append(tmpM)
        self.structures = allStructs
        if allStructs:
            return True
        else:
            return False
        #
        # Done reading the reson structs.
        #
    """
    *
    """
    def read_lines(self,fInp=''):
        """
        Reads NRT strings given in the format of $NRTSTR, $CHOOSE groups
        """
        allStructs = []
        if fInp:
            inp = open(fInp,'r')
        else:
            inp = sys.stdin

        BondTypes = {'S':1,'D':2,'T':3}

        NAtoms = 0
        inside = False
        while True:
            s = inp.readline().strip('\n')
            if not s:
                break
            if "$END" in s:
                continue
            if "STR" in s:
                inside = True
                LP, Bonds, props = {}, {}, {}
                if "!" in s:
                    all_params = s.split('!')[1]
                    for param in all_params.split(','):
                        name_value = param.split('=')
                        if len(name_value)>1:
                            props[name_value[0].strip()] = name_value[1].strip()
                continue

            if inside and "LONE" in s:
                tmp = s.split()
                for i in range(1,len(tmp)-1,2):
                    LP[tmp[i]] = tmp[i+1]
                    NAtoms = max(NAtoms,int(tmp[i]))
                #print "Lone Pairs:\n",LP
                continue

            if inside and "BOND" in s:
                tmp = s.split()
                for i in range(1,len(tmp)-1,3):
                    #print tmp,i
                    #print tmp[i],tmp[i+1],tmp[i+2]
                    BondType, smaller, higher = tmp[i], tmp[i+1],tmp[i+2]
                    NAtoms = max(NAtoms,int(higher))
                    if not higher in Bonds:
                        Bonds[higher] = {}
                    Bonds[higher][smaller]=BondType
                continue

            if "END" in s:
                inside = False
                # Fill data
                data = numpy.zeros((NAtoms,NAtoms))
                for i in LP:
                    data[int(i)-1,int(i)-1] = LP[i]
                for i in Bonds:
                    for j in Bonds[i]:
                        ii = int(i) -1
                        jj = int(j) -1
                        data[ii,jj] = BondTypes[Bonds[i][j]]
                        data[jj,ii] = data[ii,jj]
                ResStr = bondM(NAtoms,symbols=[],data=data)
                if 'name' in props:
                    ResStr.name = props['name']
                if 'symbols' in props:
                    ResStr.applyStringSymbols(props['symbols'])
                if 'weight' in props:
                    ResStr.wg = float(props['weight'])
                allStructs.append(ResStr)
        self.structures = allStructs

if __name__ == "__main__":

    DebugLevel = logging.DEBUG
    logging.basicConfig(level=DebugLevel)

    from Settings import Settings
    Top.settings = Settings(FromConfigFile = True)

    f = NRT()
    f.file = sys.argv[1]
    f.parse()

    print f
