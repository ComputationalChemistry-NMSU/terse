import logging
log = logging.getLogger(__name__)

elrad = {
        1:1.20,
        16:1.80,
        5:1.80, # Approximate!
        6:1.70,
        7:1.55,
        8:1.52,
        9:1.35
        }

at_name=('X',
'H','He',
'Li','Be','B','C','N','O','F','Ne',
'Na','Mg','Al','Si','P','S','Cl','Ar',
'K','Ca','Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Zn','Cu','Ga','Ge','As','Se','Br','Kr',
'Rb','Sr','Y','Zr','Nb','Mo','Tc','Ru','Rh','Pd','Ag','Cd','In','Sn','Sb','Te','I','Xe',
'Cs','Ba','La','Ce','Pr','Nd','Pm','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm','Yb','Lu','Hf','Ta','W','Re','Os','Ir','Pt','Au','Hg','Tl','Pb','Bi','Po','At','Rn',
'Fr','Ra','Ac','Th','Pa','U','Np','Pu','Am','Cm','Bk','Cf','Es','Fm','Md','No','Lr','Rf','Db','Sg','Bh','Hs','Mt','Ds','Rg','Uub''')

elem2num = {}
for i in range(0,len(at_name)):
    elem2num[at_name[i]] = i

BohrR = 0.5291772
H_to_kJ = 2625.5
kJ_to_kcal = 1/4.184
H_to_kcal = H_to_kJ * kJ_to_kcal

def _to_elN(el):
    """
    Converts whatever to atomic number
    """

    try: int(el)
    except:
        try: el = elem2num[el]
        except:
            log.error('Unrecognized element ' % (el))
    return el
