import sys
a = 0
for arg in sys.argv[1:]:
    z = file(arg)
    for s in z:
        a += 1
