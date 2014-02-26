br = '<br />'

brn = '<br />\n'

def tag(s, t, intag=''):
    shifted = ''
    indent = '    '
    for line in str(s).split("\n"):
        shifted += indent+line+"\n"
    return "<%(tag)s %(intag)s>\n%(tagbody)s</%(tag)s>" % {'tag': t, 'intag': intag, 'tagbody': shifted}


def img(source,width='450'):
    return brn + "<img src='%s' width=%s\n"  % (source,str(width)) + brn
