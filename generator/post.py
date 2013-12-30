import sys;
import os;
import os.path;
import utils;
import imgutils;
import shutil;
import json;
import collections;
import re;
import markup;
import codecs;
import time;

def is_picture(f):
    f = f.lower();
    ext = os.path.splitext(f)[1];
    if (not ext):
        return False;
        
    ext = ext[1:];
    if (ext == "jpg"):
        return True;
    elif (ext == "png"):
        return True;
    elif (ext == "svg"):
        return True;
    else:
        return False;

class Post:
    def __init__(self, in_dir, out_dir):
        self.directory = os.path.basename(in_dir);
        self.in_dir = in_dir;
        self.out_dir = out_dir + "/" + self.directory;
        self.small_dirname = "small"
        try:
            os.makedirs(self.out_dir + "/"  + self.small_dirname);
        except:
            pass;

        self.date = time.strptime(self.directory[:10], "%Y-%m-%d");

        self.attachments = [];

        for f in os.listdir(in_dir):
            f_full = in_dir + "/" + f;
            if (os.path.isfile(f_full)):
                if (f[-4:] == ".mml"):
                    if (hasattr(self, "page_path")):
                        utils.fatal("multipe pages found in " + in_dir);
                    self.page_path = f_full;
                    self.processHeader();
                else:
                    self.attachments.append(f);
        self.processAttachments();
                    
    # called from the renderer to replace images with their striped down version
    def image_cb(self, f):
        print("image_cb is not implemented\n");
        if (not os.path.isfile(self.in_dir + "/" + f)):
            return f;

    # given a picture name, returns the same with a .jpg extension and under the 'small' directory
    def to_small(self, f):
        name = os.path.basename(f);
        s = os.path.splitext(name);
        return self.small_dirname + "/" + s[0] + ".jpg";

    def to_abs_small(self, f):
        return self.out_dir + "/" + self.to_small(f);

    # parses the json at the beginning of the page and extracts the markup
    def processHeader(self):
        fd = utils.open_file(self.page_path, "rb");
        header_json="";
        self.markup="";
        in_header = True;
        for line in fd:
            if (in_header):
                if (line == "\n"):
                    in_header = False;
                header_json += line;
            else:
                self.markup += line;
        self.header = json.loads(header_json);
        for k in self.header:
            setattr(self, k, self.header[k]);

    # copies all attachments. 
    # for pictures, it will downscale them if needed
    def processAttachments(self):
        if (not hasattr(self, 'thumbnail')):
            for f in self.attachments:
                if (os.path.splitext(f)[0] == "thumbnail"):
                    self.thumbnail = f;

        if (not hasattr(self, 'thumbnail')):
            if (len(self.attachments) == 0):
                utils.fatal("no thumbnail can be found in " + self.in_dir + "\n");
            print("warning: using " + self.attachments[0] + " as thumbnail");
            self.thumbnail = self.attachments[0];
        
        for f in self.attachments:
            attachment_path = self.out_dir + "/" + f;
            if (not os.path.isfile(attachment_path)):
                print("processing attachment " + attachment_path + "...");
                shutil.copy(self.in_dir + "/" + f,  attachment_path);

            if (is_picture(f)):
                self.processPicture(f);
            
    # special case for date_str
    def __getattribute__(self, name):
        if (name == "date_str"):
            return time.strftime("%B %d, %Y", self.date)
        else:
            return object.__getattribute__(self, name)

    def processPicture(self, f):
        small_abs_path = self.to_abs_small(f);
        input_abs_path = self.in_dir + "/" + f; 
        if (not os.path.isfile(small_abs_path)):
            # converts to jpeg and ensure the final resolution is not more than 1 MPix
            imgutils.ensure_less_than_one_megapixel(input_abs_path, small_abs_path);

        if (f == self.thumbnail):
            imgutils.generate_thumbnail(input_abs_path, self.out_dir);

    def render(self, fd):
        fd.write('<div class="post">\n');
        markup.render(self.markup, fd, self.image_cb);
        fd.write('</div>\n');
