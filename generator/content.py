import sys;
import os;
import os.path;
import utils;
import imgutils;
import shutil;
import json;
import collections;
import re;
import markdown;
import codecs;
import time;
import markdown;

code = """var getContent = function getContent(centerer)
{
    var post = $("<div>");
    post.attr("id", "post");
    post.html(contentHtml);
    centerer.append(post);

    return;
}

var getDepth = function getDepth() {
    return "../../";
}
""";

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

class Content(object):
    def __init__(self, in_base_path, in_path, out_path):
        self.directory = os.path.basename(in_path);
        self.in_path = in_path;
        self.out_path = out_path + "/" + self.directory;
        self.small_dirname = "small";
        self.date_str = "";
        try:
            os.makedirs(self.out_path + "/"  + self.small_dirname);
        except:
            pass;

        try:
            self.date = time.strptime(self.directory[:10], "%Y-%m-%d");
        except ValueError as e:
            self.date = None;
            pass;

        self.attachments = [];

        for f in os.listdir(in_path):
            f_full = in_path + "/" + f;
            if (os.path.isfile(f_full)):
                if (f[-4:] == ".mml"):
                    if (hasattr(self, "page_path")):
                        utils.fatal("multipe content found in " + in_path);
                    self.page_path = f_full;
                    self.processHeader();
                else:
                    self.attachments.append(f);
        self.processAttachments();
        
        # generate app.js 
        common_fd = utils.open_file(in_base_path + "/common.js", "rb");
        app_fd = utils.open_file(self.out_path + "/app.js", "wb");
        escaped_html = self.html.replace("\"", "\\\"").replace("\n", "\\n");
        app_fd.write("contentHtml = \"" + escaped_html + "\";\n\n");
        if (not self.date):
            app_fd.write(code.replace("\"post\"", "\"page\""));
        else:
            app_fd.write(code);
        app_fd.write(common_fd.read());
        
        # and index.html
        utils.generate_index(self.title, "../../", self.out_path + "/index.html");
        
                    
    # called from the renderer to replace images with their striped down version
    def image_cb(self, f):
        print("image_cb is not implemented\n");
        if (not os.path.isfile(self.in_path + "/" + f)):
            return f;

    # given a picture name, returns the same with a .jpg extension and under the 'small' directory
    def to_small(self, f):
        name = os.path.basename(f);
        s = os.path.splitext(name);
        return self.small_dirname + "/" + s[0] + ".jpg";

    def to_abs_small(self, f):
        return self.out_path + "/" + self.to_small(f);

    # parses the json at the beginning of the page and extracts the markdown
    def processHeader(self):
        fd = utils.open_file(self.page_path, "rb");
        header_json="";
        m="";
        in_header = True;
        for line in fd:
            if (in_header):
                if (line == "\n"):
                    in_header = False;
                header_json += line;
            else:
                m += line;
        try:
            self.header = json.loads(header_json);
        except ValueError as e:
            utils.fatal("malformed content header in " + self.page_path + ":\n" + str(e));
                        
        for k in self.header:
            setattr(self, k, self.header[k]);

        self.html = markdown.markdown(m);

    # copies all attachments. 
    # for pictures, it will downscale them if needed
    def processAttachments(self):
        if (not hasattr(self, 'thumbnail')):
            for f in self.attachments:
                if (os.path.splitext(f)[0] == "thumbnail"):
                    self.thumbnail = f;

        if (not hasattr(self, 'thumbnail')):
            if (len(self.attachments) == 0):
                utils.fatal("no thumbnail can be found in " + self.in_path + "\n");
            print("warning: using " + self.attachments[0] + " as thumbnail");
            self.thumbnail = self.attachments[0];
        
        for f in self.attachments:
            attachment_path = self.out_path + "/" + f;
            if (not os.path.isfile(attachment_path)):
                print("processing attachment " + attachment_path + "...");
                shutil.copy(self.in_path + "/" + f,  attachment_path);

            if (is_picture(f)):
                self.processPicture(f);
            
    # special case for date_str
    def __getattribute__(self, name):
        #print("getattr " + name + "\n");
        if (name == "date_str"):
            if (self.date):
                return time.strftime("%B %d, %Y", self.date)
            else:
                return "none";
        else:
            return object.__getattribute__(self, name)

    def processPicture(self, f):
        small_abs_path = self.to_abs_small(f);
        input_abs_path = self.in_path + "/" + f; 
        if (not os.path.isfile(small_abs_path)):
            # converts to jpeg and ensure the final resolution is not more than 1 MPix
            imgutils.ensure_less_than_one_megapixel(input_abs_path, small_abs_path);

        if (f == self.thumbnail):
            imgutils.generate_thumbnail(input_abs_path, self.out_path);
