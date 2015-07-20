import re
import logging
log = logging.getLogger(__name__)

class BetterFile(file):

    def __init__(self,name,mode='r'):
        self.s = ''
        self.lnum = 0
        self.ssplit = []
        self.sstrip = ''
        try:
            file.__init__(self,name,mode)
            log.debug('%s was opened for reading' %(name))
        except:
            log.error('Cannot open %s for reading' %(name))


    def skip(self,n=1):
        for _ in range(n): self.next()


    def skip_until(self,pattern,Offset=0,regexp=False):
        """
        Reads the file line by line until one of the patterns found
        (pattern might be a string with substring to be looked for,
        or a list of such substrings)
        If pattern is a list, then a returning value
        is an index of the matching string
        :param re: Boolean; treat patterns as regexps
        """
        instance_hit = 0
        if pattern:
            if not isinstance(pattern,(list,tuple)):
                ps = [pattern,]
            else:
                ps = pattern
            while True:
                for i in range(len(ps)):
                    if regexp:
                        hit = re.search(ps[i],self.s)
                    else:
                        hit = (ps[i] in self.s)
                    if hit:
                        instance_hit = i
                        break
                else:
                    self.next()
                    continue
                break
        else:
            while self.s.strip() != '':
                self.next()
        self.skip(Offset)
        return instance_hit


    def nstrip(self):
        self.sstrip =  self.next().strip()
        return self.sstrip


    def nsplit(self):
        self.ssplit = self.nstrip().split()
        return self.ssplit


    def next(self):
        self.s = file.next(self)
        self.lnum += 1
        return self.s

    def getBlock(self,StartMatch='',StartOffset=0,EndMatch='',EndOffset=-1):
        """
        reads a textblock from the file
        #
        #
        #  Say, StartOffset = 3, and EndOffset = -1:
        #   StartMatch : 0 : -
        #   Junk       : 1 : -
        #   Junk       : 2 : -
        #   Info       : 3 : +
        #   Info       :   : +
        #   Info       :-1 : +
        #   EndMatch   : 0 : -
        #   Other      : 1 : -
        #   Other      : 2 : -
        #
        #  In this case, only strings marked by '+' sign will be extracted
        #  If StartMatch is not defined, block will start at current position+StartOffset
        #  If EndMatch is not defined, block will end at an empty string
        """
        # Positioning
        if StartMatch:
            self.skip_until(StartMatch)
        self.skip(StartOffset)

        # Define criteria for stop
        def SecondMatch(match,s):
            if match and match in s:
                return True
            if match=='' and s.strip()=='':
                return True
            return False

        # Fill array
        ss = []
        while not SecondMatch(EndMatch,self.s):
            ss.append(self.s.strip())
            self.next()

        # Add lines after the stop match
        for i in range(EndOffset+1):
            ss.append(self.s)
            self.nstrip()

        return ss
#
#
#
#
#
if __name__ == "__main__":
    import sys
    DebugLevel = logging.DEBUG
    logging.basicConfig(level=DebugLevel)

    def tst(args):
        a = 0
        for arg in args:
            z = BetterFile(arg)
            #z = file(arg)
            for s in z:
                a += 1

    z = BetterFile(sys.argv[1])
    #d = z.getBlock(StartMatch='Summary of Natural Population Analysis:',StartOffset=6,EndMatch='===')
    d = z.getBlock(StartMatch='Summary of Natural Population Analysis:',StartOffset=6,EndMatch='')
    for r in d:
        print r

    #import profile
    #tst(sys.argv[1:])
    #profile.run('tst(sys.argv[1:])')
