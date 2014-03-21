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
import time;
import urlparse;
from xml.sax.saxutils import escape

class Struct(object):
    def __init__(self, entries): 
        self.__dict__.update(entries)
    
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

            c = content.Content(self.in_base_path, in_path + "/" + d, out_path);
            c.relpath = directory + "/" + c.directory;
            c.type = directory;
            getattr(self, directory).append(c);
            context = {};
            context["content"] = c;
            context["page"] = Struct({"title": c.title, "template": "content.template", "depth": "../../"});
            self.process_file("index.template", c.relpath + "/index.html", context);

    def replace_commands(self, template, context):
        def match_cb(m, self=self):
            do_esc = True;
            s = m.group(1);
            if (s[0] == "-"):
                do_esc = False;
                s = s[1:];

            # mouhahaha 
            try:
                r = eval(s, globals(), context);
                if (do_esc):
                    #print("before " + r);
                    r = escape(r);
                    #print("after " + r);
                return r;
            except:
                utils.fatal("error on eval(" + m.group(1) + ")");

        return utils.re_replace_all("%{([^}]*)}", template, match_cb);

    def include(self, in_relpath, context):
        #print("including: " + in_relpath);
        output_str = "";
        context["blog"] = self.blog;
        def include2(relpath):
            return self.include(relpath, context);

        context["include"] = include2;

        fd = utils.open_file(self.in_base_path + "/" + in_relpath, "rb");
        lines = collections.deque(fd.readlines());
        while (len(lines) > 0):
            line = lines.popleft();
            # XXX: this is not recursive
            if (re.search("#{for_each_post}", line)):
                template = "";
                while (len(lines) > 0):
                    line = lines.popleft();
                    if (re.search("#{done}", line)):
                        for p in self.posts:
                            context["post"] = p;
                            output_str += self.replace_commands(template, context);
                        del context["post"];
                        break;
                    template += line;
            
            else:
                 output_str += self.replace_commands(line, context);

        #print("include returned'" + output_str + "'");
        return output_str;

    def process_file(self, in_relpath, out_relfpath, context):
        print("=== " + out_relfpath + " ===");
        out_fpath = self.out_base_path + "/" + out_relfpath;
        utils.makedirs(os.path.dirname(out_fpath));
        utils.open_file(out_fpath, "wb").write(self.include(in_relpath, context));
        
    def generate_feed(self):
        self.process_file("feed.template", "feed/index.html", {});
        
    def generate_home(self):
        # sort posts, in reverse order: latest first
        self.posts.sort(cmp=lambda x,y: cmp(y.date, x.date));

        index = 0;
        for p in self.posts:
            p.index = index;
            index += 1;

        context = {};
        context["page"] = Struct({"title": self.blog.description, "depth": "/", "template":"home.template"});
        self.process_file("index.template", "index.html", context);

    def generate(self, in_base_path, out_base_path):
        self.in_base_path = in_base_path;
        self.out_base_path = out_base_path;
        
        utils.makedirs(out_base_path);                
        imgutils.init(in_base_path);
        utils.init(in_base_path);
        
        self.blog = Struct(json.load(utils.open_file(self.in_base_path + "/blog.json")));

        # copy static content
        cmd = "cp -rf " + in_base_path + "/static/* " + out_base_path;
        print("copy static content: " + cmd)
        proc = utils.execute_shell(cmd);
        
        # 'dynamic' content
        for c in ["sticky", "posts"]:
            setattr(self, c, []);
            self.generate_content(c);        
        
        # home page
        self.generate_home();

        # feed
        self.generate_feed();
        
if(__name__ == "__main__"):
    if (len(sys.argv) < 3):
        print("usage: " + sys.argv[0] + " [input dir] [output dir]");
        sys.exit(1);

    Generator().generate(sys.argv[1], sys.argv[2]);


