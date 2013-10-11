import os;
import os.path;
import utils;
import shutil;
import json;

def isPicture(f):
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
        post_name = os.path.basename(in_dir);
        self.in_dir = in_dir;
        self.out_dir = out_dir + "/" + post_name;
        self.attachments_dir = self.out_dir + "/attachments";
        try:
            os.makedirs(self.attachments_dir);
        except:
            pass;

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
                    
    # parses the json at the beginning of the page and extracts the markup
    def processHeader(self):
        fd = open(self.page_path, "r");
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
        header = json.loads(header_json);
        self.title = header['title'];
        if ('thumbnail' in header):
            self.thumbnail = header['thumbnail'];

    # copies all attachments. 
    # for pictures, it will downscale them if needed
    def processAttachments(self):
        for f in self.attachments:
            #make all attachments lowercase, I find it nicer
            attachment_path = self.attachments_dir + "/" + f.lower();
            if (not os.path.isfile(attachment_path)):
                print("attachment " + attachment_path);
                shutil.copy(self.in_dir + "/" + f,  attachment_path);

            if (isPicture(f)):
                self.processPicture(f.lower());
            
    def processPicture(self, f):
        name = os.path.splitext(f)[0];
        one_m_path = self.attachments_dir + "/" + name + "_1m.jpg";
        one_m_bw_path = self.attachments_dir + "/" + name + "_1m_bw.jpg";
    
        if (not os.path.isfile(one_m_path)):
            # converts to jpeg and ensure the final resolution is not more than 1 MPix
            proc = utils.Popen("convert -resize @1000000> " + self.attachments_dir + "/" + f + " " + one_m_path);
            if (proc.returncode != 0):
                print("could not convert " + f +": " + proc.err);
                os.exit(1);

        if (not os.path.isfile(one_m_bw_path)):
            proc = utils.Popen("convert " + one_m_path + " -colorspace Gray " + one_m_bw_path);
            if (proc.returncode != 0):
                print("could not convert " + f +": " + proc.err);
                os.exit(1);

    def render(self, fd):
        fd.write('<div class="post">\n');
        i = 0;
        lines = self.markup.splitlines();
        while (i < len(lines)):
            line = lines[i];
            fd.write(line + "\n");
            i = i + 1;
        fd.write('<div class="post">\n');
