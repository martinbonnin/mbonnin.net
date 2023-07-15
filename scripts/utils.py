import sys;
sys.dont_write_bytecode = True
import subprocess;
import os;
import errno;
from html.parser import HTMLParser
import cgi;
import codecs;
import re;
from xml.sax.saxutils import escape

def execute_shell(args):
    #print("execute_shell: " + args);
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True);
    class Result(object):
        out = ''
        err = ''
        returncode = ''
    
    ret = Result()
    (ret.out, ret.err) = proc.communicate()
    ret.returncode = proc.returncode;
    return ret;

def init(base):
    global in_base_path;
    in_base_path = base;

def unescape(s):
    return HTMLParser.HTMLParser().unescape(s);

def escape(s):
    return cgi.escape(s);

def open_file(path, _mode="rb"):
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

def makedirs(path):
    try:
        os.makedirs(path);
    except OSError as e:
        if (e.errno != errno.EEXIST):
            fatal("cannot make dir");
