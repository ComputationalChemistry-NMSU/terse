import logging
log = logging.getLogger(__name__)

from Top import Top
import Parsers.XYZ


class Geom(Top):

    def __init__(self):
        self.comment = ''
        self.coord = []
        self.header_natoms = 0
        self.props = []
        self.atprops = []
        self.to_kcalmol = 1.

    def __nonzero__(self):
        """
        Is nonzero if has at least one atom
        """

        if self.coord:
            return True
        return False


    def __len__(self):
        """
        Returns number of atoms in a structure
        """

        return len(self.coord)


    def __getitem__(self,item):
        """
        Return an atom by index
        """

        return self.coord[item]


    # It was not a good realization of __str__, so I blocked it
    def _str__(self):
        """
        Print short text information
        """

        s = '%i atoms;   Comment=\'%s\'   ' % (len(self.coord),self.comment)
        s += self.propsToString() + '\n'
        return s


    def addProp(self,a,v):
        if not a in self.props:
            self.props.append(a)
        setattr(self,a,v)

    def addAtProp(self,ap,visible=True):
        """
        :param v: object of class AtomicProps
        """
        an = ap.attrname
        if visible and not an in self.atprops:
            self.atprops.append(an)
        setattr(self,an,ap)


    def propsToString(self,ShowComment = False):
        """
        Returns string representation of properties
        """

        if ShowComment:
            s = self.comment
        else:
            s = ''
        for a in self.props:
            s += '%s= %s   ' % (a,getattr(self,a))
        return s


    def parseComment(self,s):
        """
        Fetches parameters from a string.
        Delimiter between fields is space, and format is 'Arg = Value' with any number of spaces before/afer equal sign
        """

        result = {}
        new_comment = s
        # Add some aliases
        syn = {
                'e'    : ('en','energy'),
                'grad' : ('gradient',)
              }
        #delimiters = ('=',':') 
        delimiters = ('=')
        for delim in delimiters:
            s2 = s.replace(delim,' '+delim+' ').split()
            for i in range(1,len(s2)-1):
                if s2[i] == delim:
                    arg,val = s2[i-1],s2[i+1]
                    arl = str(arg).lower()
                    # Try to make value float
                    try:
                        val = float(val)
                    except ValueError:
                        pass
                    # Look for synonyms
                    for a in syn:
                        if arl in syn[a]:
                            arl = a
                    # Set new attribute
                    setattr(self,arl,val)
                    if not arl in self.props:
                        self.props.append(arl)
                    # Remove parsed parameter from comment
                    #new_comment = re.sub('%s\s*%s\s*%s'%(arg,delim,val),'',new_comment).strip() # TODO figure out later how to make it work with variables containing parentheses
                    self.comment = ''
                #self.comment += new_comment.strip() 



    def write(self,fname,vectors=None):
        """
        The actual function that writes coords is in the XYZ parser,
        and it takes an object of class ListGeoms as an argument.
        Here, we have only one geometry, so we supposed to create
        an instance of ListGeoms. However, we can make a trick
        by providing a simple list instead of ListGeoms to
        write coords
        """
        c = Parsers.XYZ.XYZ()
        webpath = c.write(fname,geoms=[self],vectors=vectors)
        return webpath
