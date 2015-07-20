%nproc=2
%mem=1Gb
%chk=ts-irc-F.chk
#p pm3 irc(calcfc,forward,maxpoint=200,stepsize=5,maxcyc=200) scf(xqc,maxcyc=200,fermi)
#p  geom(allcheck)

