#!/usr/bin/env python
import sys

if (len(sys.argv) <= 1) :
    print(sys.argv[0] + " mime.types");
    sys.exit(1)
    
fd = open(sys.argv[1])
lines = fd.readlines()

print("types = {")
for line in lines:
    line = line.rstrip()
    if (line[0] == "#"):
        continue
    c = line.split()
    c = [v for v in c if c != "" ]
    for i in range(1, len(c)):
        print('".' + c[i] + '": "' + c[0] + '",');

print("}")
