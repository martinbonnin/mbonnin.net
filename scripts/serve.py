#!/usr/bin/env python

import BaseHTTPServer
import SocketServer
import pdb
import mime
import os
import logging
import subprocess
import utils
import threading

PORT = 8080

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    extensions_map = mime.types;
    #add the default type
    extensions_map[''] = "application/octet-stream";

    def guess_type(self, path):
        (root, ext) = os.path.splitext(path);
        try:
            return self.extensions_map[ext]
        except:
            return self.extensions_map['']

    def do_GET(self):
        #print("got request for " + self.path);
        #pdb.set_trace();
        path = site_dir + self.path;
        if (os.path.isdir(path)):
            if (path[-1] != "/"):
                path += "/"
                self.send_response(301);
                self.send_header("Location", self.path + "/");
                self.end_headers();
                return;out               
            if (self.path == "/feed/"):
                path += "feed.xml";
            else:
                path += "index.html"
        
        if (path.find("index.html") != -1):
            print("refresh...");
            lock.acquire();
            cmd = script_dir + "/generate.py " + skeleton_dir + " " + site_dir;
            proc = utils.execute_shell(cmd);
            if (proc.returncode != 0):
                self.send_response(500)
                self.end_headers();
                self.wfile.write("out:\n")
                self.wfile.write(proc.out)
                self.wfile.write("err:\n")
                self.wfile.write(proc.err)
                lock.release()
                return;
            lock.release()
                
        try:
            fd = open(path);
        except:
            fd = None

        if (fd):
            data = fd.read();
            self.send_response(200);
            self.send_header("Content-type", self.guess_type(path));
            self.send_header("Content-length", len(data));
            self.end_headers();
            self.wfile.write(data);
        else:
            self.send_response(404);
            self.end_headers();
            self.wfile.write("cannot find " + path + "\n");
            if (self.path == "/"):
                self.wfile.write("try reloading...");
        
class MyServer(SocketServer.TCPServer):
    allow_reuse_address = True

script_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.realpath(script_dir + "/..")
site_dir = os.path.realpath(base_dir + "/site")
skeleton_dir = os.path.realpath(base_dir + "/skeleton")

lock = threading.Lock()

try:
    os.mkdir(site_dir);
except OSError as e:
    pass;

httpd = MyServer(("", PORT), MyHandler)

print "script_dir: " + script_dir
print "base_dir: " + base_dir
print "site_dir: " + site_dir
print "skeleton_dir: " + skeleton_dir
print ""
print "website served at: http://localhost:%d"% PORT
httpd.serve_forever()
