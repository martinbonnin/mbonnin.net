#!/usr/bin/env python
import sys;
sys.dont_write_bytecode = True
import post;
import os;
import codecs;
import os.path;
import json;
import utils;
import imgutils;
import collections;
import re;

class Generator:
    def __init__(self):
        self.posts=[]

    def process_file(self, in_file, out_file):
        out_fd = utils.open_file(self.out_dir + "/" + out_file, "wb");
        in_fd = utils.open_file(self.in_dir + "/" + in_file, "rb");

        lines = collections.deque(in_fd.readlines());
        while (len(lines) > 0):
            line = lines.popleft();
            # XXX: this is not recursive
            if (re.search("#{for_each_post}#", line)):
                template = "";
                while (len(lines) > 0):
                    line = lines.popleft();
                    if (re.search("#{done}#", line)):
                        for p in self.posts:
                            self.post = p;
                            out_fd.write(self.replace_commands(template));
                        break;
                    template += line;
            
            else:
                 out_fd.write(self.replace_commands(line));
                

    def generate(self, in_dir, out_dir):
        self.in_dir = in_dir;
        self.out_dir = out_dir;
        posts_dir = in_dir + "/posts";
        
        try:
            os.mkdir(out_dir);
        except:
            pass;
                
        imgutils.init(in_dir);

        # copy resources and index.html
        proc = utils.Popen("cp -rf " + in_dir + "/res " + out_dir);
        proc = utils.Popen("cp -rf " + in_dir + "/index.html " + out_dir);
         
        # parse posts
        for d in os.listdir(posts_dir):
            if (not os.path.isdir(posts_dir + "/" + d)):
                continue;

            print("=== post " + d + "===");
            self.posts.append(post.Post(posts_dir + "/" + d, out_dir + "/posts"));

        # sort posts, in reverse order: latest first
        self.posts.sort(cmp=lambda x,y: cmp(y.date, x.date));

        # and write the home app.js. It is the concatenation of:
        #  1. json dump of all posts
        #  2. page specific javascript
        #  3. common javascript
        home_fd = utils.open_file(self.in_dir + "/home.js", "rb");
        common_fd = utils.open_file(self.in_dir + "/common.js", "rb");
        app_fd = utils.open_file(self.out_dir + "/app.js", "wb");

        app_fd.write("posts = ");
        posts = [{k: getattr(p, k, None) for k in ["directory", "title", "date_str", "description"]} for p in self.posts];
        json.dump(posts, app_fd, indent=4);
        app_fd.write(";\n");
        app_fd.write(home_fd.read());
        app_fd.write(common_fd.read());
        
if(__name__ == "__main__"):
    if (len(sys.argv) < 3):
        print("usage: " + sys.argv[0] + " [input dir] [output dir]");
        sys.exit(1);

    Generator().generate(sys.argv[1], sys.argv[2]);


