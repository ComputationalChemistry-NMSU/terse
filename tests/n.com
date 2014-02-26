%nproc=8
%mem=12Gb
%chk=n.chk
#p pbe1pbe/gen opt freq


1 1
@n.xyz

@/home/MARQNET/talipovm/basis-library/def2-SV(P)+d.gbs

--link1--
%nproc=8
%mem=12Gb
%chk=n.chk
#p pbe1pbe/gen opt(readfc) freq pop(nboread) geom(check)


1 1

@/home/MARQNET/talipovm/basis-library/def2-TZVPPD.gbs

 $nbo archive file=n $end


