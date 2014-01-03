import sys;
sys.dont_write_bytecode = True
import subprocess;
import os;
import HTMLParser;
import cgi;
import codecs;
import re;
from xml.sax.saxutils import escape

class Popen:
    def __init__(self, string):
        args = string.split(" ");
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
        (self.out, self.err) = proc.communicate()
        self.returncode = proc.returncode;

def init(base):
    global in_base_path;
    in_base_path = base;

def unescape(s):
    return HTMLParser.HTMLParser().unescape(s);

def escape(s):
    return cgi.escape(s);

def open_file(path, _mode):
    return codecs.open(path, encoding='utf-8', mode=_mode);

def re_replace_all(re_str, template, match_cb):
    start = 0;
    result = "";
    while (True):
        m = re.search(re_str, template[start:]);
        if (not m):
            result += template[start:];
            return result;
        result += template[start:start + m.start()];
        result += match_cb(m);
        start += m.end();

def fatal(text):
    print(text);
    sys.exit(1);

def generate_index(title, depth, out_path):
    in_fd = open_file(in_base_path + "/index.html", "rb");
    out_fd = open_file(out_path, "wb");
    a = in_fd.read().replace("%TITLE", escape(title));
    a = a.replace("%DEPTH", depth);
    out_fd.write(a);        
