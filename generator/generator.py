#!/bin/python
import sys;
sys.dont_write_bytecode = True
import post;
import os;
import os.path;

if(__name__ == "__main__"):
    if (len(sys.argv) < 3):
        print("usage: " + sys.argv[0] + " [input dir] [output dir]");
        sys.exit(1);

    in_dir = sys.argv[1];
    out_dir = sys.argv[2];
    published_dir = in_dir + "/published";

    try:
        os.mkdir(out_dir);
    except:
        pass;
    
    for d in os.listdir(published_dir):
        if (not os.path.isdir(published_dir)):
            continue;

        p = post.Post(published_dir + "/" + d, out_dir);
        fd = open(p.out_dir + "/index.html", "w");
        p.render(fd);

