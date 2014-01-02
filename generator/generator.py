#!/usr/bin/env python
import sys;
sys.dont_write_bytecode = True
import content;
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
        pass;                

    def generate_content(self, directory):
        in_path = self.in_base_path + "/" + directory;
        out_path = self.out_base_path + "/" + directory;

        # parse content
        for d in os.listdir(in_path):
            if (not os.path.isdir(in_path + "/" + d)):
                continue;

            print("=== " + directory + "/" + d + "===");
            c = content.Content(self.in_base_path, in_path + "/" + d, out_path);
            c.path = directory + "/" + c.directory;
            getattr(self, directory).append(c);
        
    def generate_home(self):
        # sort posts, in reverse order: latest first
        self.posts.sort(cmp=lambda x,y: cmp(y.date, x.date));

        # write the home app.js. It is the concatenation of:
        #  1. json dump of all posts
        #  2. page specific javascript
        #  3. common javascript
        home_fd = utils.open_file(self.in_base_path + "/home.js", "rb");
        common_fd = utils.open_file(self.in_base_path + "/common.js", "rb");
        app_fd = utils.open_file(self.out_base_path + "/app.js", "wb");

        app_fd.write("posts = ");
        posts = [{k: getattr(p, k, None) for k in ["path", "title", "date_str", "description"]} for p in self.posts];
        json.dump(posts, app_fd, indent=4);
        app_fd.write(";\n");
        app_fd.write(home_fd.read());
        app_fd.write(common_fd.read());

    def generate(self, in_base_path, out_base_path):
        self.in_base_path = in_base_path;
        self.out_base_path = out_base_path;
        
        try:
            os.mkdir(out_base_path);
        except:
            pass;
                
        imgutils.init(in_base_path);

        # copy static content
        utils.Popen("cp -rf " + in_base_path + "/res " + out_base_path);
        utils.Popen("cp -rf " + in_base_path + "/index.html " + out_base_path);
         
        # 'dynamic' content
        for c in ["pages", "posts"]:
            setattr(self, c, []);
            self.generate_content(c);
        
        # home page
        self.generate_home();
        
if(__name__ == "__main__"):
    if (len(sys.argv) < 3):
        print("usage: " + sys.argv[0] + " [input dir] [output dir]");
        sys.exit(1);

    Generator().generate(sys.argv[1], sys.argv[2]);


