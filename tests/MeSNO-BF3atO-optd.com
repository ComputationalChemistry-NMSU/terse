%nproc=8
%mem=12gb
%chk=MeSNO-BF3atO-optd.chk
#p pbe1pbe/gen scf(xqc) pop(savenbos,nboread)


0 1
@MeSNO-BF3atO-optd.xyz

@/home/MARQNET/talipovm/basis-library/def2-SV(P)+d.gbs

 $nbo archive file=MeSNO-BF3atO-optd $end



