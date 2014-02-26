import os
import logging
log = logging.getLogger(__name__)

class Top:
    def __str__(self,depth=0):
        if not self.settings.full:
            return self.str_short()

        shift = ' '*4*depth
        shift_p1 = ' '*4*(depth+1)

        s = '\n' + shift + 'Object of "%s" class\n' % (self.__class__)
        for a,v in sorted(self.__dict__.iteritems()):
            if not v:
                continue

            if isinstance(v,Top):
                # If another object of Top class is attached, then recursively call __str__ with increased offset
                vstr = v.__str__(depth+1)
            elif isinstance(v,(list,tuple)):
                # objects of Top might be stored in lists, so we ought to look there as well
                vstr = '['
                for v2 in v:
                    if isinstance(v2,Top):
                        vstr += v2.__str__(depth+1) + '\n'  + shift_p1
                    else:
                        vstr += "'%s'" % (v2)
                    vstr += ','
                vstr += ']'
            else:
                vstr = "'%s'" % (v)

            s+= shift + '%s = ' %(a)
            s+= vstr + '\n'
        return s[:-1]

    def str_short(self):
        s = '\n' + 'Object of "%s" class\n' % (self.__class__)
        for a,v in sorted(self.__dict__.iteritems()):
            if not v:
                continue
            s+= "%s = '%s'\n" %(a,v)
        return s[:-1]

    def parse(self, *args):
        log.error('Requested parser has not been implemented yet')

    def usage(self, *args):
        log.error('No CPU statistics can be collected for this parser')

    def postprocess(self):
        pass

    def webData(self, *args):
        log.error('Web output has not been implemented yet')
        return '',''


if __name__ == "__main__":
    from Settings import Settings
    top = Top(Settings())
    print top.exts
    parser = top.assignType(['file','a.log'])
    print parser
