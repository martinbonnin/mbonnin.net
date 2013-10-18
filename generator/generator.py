#!/bin/python
import sys;
sys.dont_write_bytecode = True
import post;
import os;
import codecs;
import os.path;
import json;
import utils;
import collections;
import re;

class Generator:
    def __init__(self):
        self.posts=[]

    def column_width(self, count):
        count *= self.blog_parameters['column_width'];
        if (count < 0):
            count = 100 + count;
        return str(count) + "%";

    def replace_commands(self, template):
        def match_cb(m, self=self):
            # mouhahaha 
            if (hasattr(self, "post")):
                post = self.post;
            blog_parameters = self.blog_parameters;
            column_width = self.column_width;
            return eval(m.group(1));

        return utils.re_replace_all("%{([^}]*)}%", template, match_cb);

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
        published_dir = in_dir + "/published";
        
        try:
            os.mkdir(out_dir);
        except:
            pass;
        
        # parse blog_parameters
        blog_parameters_fd = utils.open_file(in_dir + "/blog_parameters.json", "rb");
        self.blog_parameters = json.load(blog_parameters_fd);
        
        # copy resources
        proc = utils.Popen("cp -rf " + in_dir + "/res " + out_dir);        
         
        # parse posts
        for d in os.listdir(published_dir):
            if (not os.path.isdir(published_dir)):
                continue;

            self.posts.append(post.Post(published_dir + "/" + d, out_dir));

        # sort posts
        self.posts.sort(cmp=lambda x,y: cmp(y.date, x.date));

        self.process_file("home.html", "index.html");
        self.process_file("style.css", "style.css");                    
        
if(__name__ == "__main__"):
    if (len(sys.argv) < 3):
        print("usage: " + sys.argv[0] + " [input dir] [output dir]");
        sys.exit(1);

    Generator().generate(sys.argv[1], sys.argv[2]);


