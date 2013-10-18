import sys;
import os;
import os.path;
import utils;
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
        self.attachments_dirname = "attachments"
        try:
            os.makedirs(self.out_dir + "/"  + self.attachments_dirname);
        except:
            pass;

        self.date = time.strptime(self.directory[:10], "%Y-%m-%d");

        self.attachments = [];

        for f in os.listdir(in_dir):
            f_full = in_dir + "/" + f;
            if (os.path.isfile(f_full)):
                if (f == "page.mml"):
                    self.page_path = f_full;
                    self.processHeader();
                else:
                    self.attachments.append(f);
        self.processAttachments();
                    
    def to_attachment(self, f, one_m=False, bw=False):
        name = os.path.basename(f);
        if (not os.path.isfile(self.in_dir + "/" + name)):
            return f;
        ret = "attachments/";
        
        if (is_picture(name)):
            s = os.path.splitext(name);
            ret += s[0].lower();
            ext = s[1].lower();

            if (one_m):
                ret += "_1m";
                ext = ".jpg";
            if (bw):
                ret += "_bw";
                ext = ".jpg";
            return ret + ext;
        else:
            return ret + name.lower();

    def to_abs_attachment(self, f, one_m=False, bw=False):
        return self.out_dir + "/" + self.to_attachment(f, one_m, bw);

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
        self.title = self.header['title'];
        if ('thumbnail' in self.header):
            self.thumbnail_original = self.header['thumbnail'];

    # copies all attachments. 
    # for pictures, it will downscale them if needed
    def processAttachments(self):
        if (not hasattr(self, 'thumbnail_original')):
            for f in self.attachments:
                if (os.path.splitext(f)[0].lower() == "thumbnail"):
                    self.thumbnail_original = f;

        if (not hasattr(self, 'thumbnail_original')):
            print("warning: using " + self.attachments[0] + " as thumbnail");
            self.thumbnail_original = self.attachments[0];
        
        for f in self.attachments:
            #make all attachments lowercase, I find it nicer
            attachment_path = self.to_abs_attachment(f);
            if (not os.path.isfile(attachment_path)):
                print("processing attachment " + attachment_path + "...");
                shutil.copy(self.in_dir + "/" + f,  attachment_path);

            if (is_picture(f)):
                self.processPicture(f);
            
    def processPicture(self, f):
        one_m_path = self.to_abs_attachment(f, True);    
        if (not os.path.isfile(one_m_path)):
            # converts to jpeg and ensure the final resolution is not more than 1 MPix
            proc = utils.Popen("convert -resize @1000000> " + self.in_dir + "/" + f + " " + one_m_path);
            if (proc.returncode != 0):
                print("could not convert " + f +": " + proc.err + ":" + proc.out);
                sys.exit(1);

        if (f == self.thumbnail_original):
            self.thumbnail = self.to_attachment(f, True, True);
            thumbnail_path = self.to_abs_attachment(f, True, True);
            if (not os.path.isfile(thumbnail_path)):
                proc = utils.Popen("convert -resize 512x512^ -gravity center -extent 512x512 " + one_m_path + " -colorspace Gray " + thumbnail_path);
                if (proc.returncode != 0):
                    print("could not convert " + f +": " + proc.err);
                    sys.exit(1);


    def render(self, fd):
        fd.write('<div class="post">\n');
        markup.render(self.markup, fd, self.to_attachment);
        fd.write('</div>\n');
