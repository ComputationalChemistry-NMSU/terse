%nproc=8
%mem=12Gb
%chk=ts-irc-R.chk
#p b3lyp/chkbasis irc(calcfc,reverse,maxpoint=200,stepsize=5,maxcyc=200) scf(xqc,maxcyc=200,fermi)
#p  geom(allcheck)

