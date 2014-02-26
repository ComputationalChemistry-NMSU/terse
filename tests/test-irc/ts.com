%nproc=2
%mem=1Gb
%chk=ts.chk
#p pm3  opt(ts,calcfc,noeigentest) freq


0 1
@ts.xyz


