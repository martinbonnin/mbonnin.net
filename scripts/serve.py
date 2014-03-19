#!/usr/bin/env python

import BaseHTTPServer
import SocketServer
import pdb
import mime
import os
import logging

PORT = 8080

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    extensions_map = mime.types;
    #add the default type
    extensions_map[''] = "application/octet-sam";

    def guess_type(self, path):
        (root, ext) = os.path.splitext(path);
        try:
            return self.extensions_map[ext]
        except:
            return self.extensions_map['']

    def do_GET(self):
        #print("got request for " + self.path);
        #pdb.set_trace();
        path = "./site" + self.path;
        if (os.path.isdir(path)):
            if (path[-1] != "/"):
                path += "/"
                self.send_response(301);
                self.send_header("Location", self.path + "/");
                self.end_headers();
                return;
                
            path += "index.html"
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
        
class MyServer(SocketServer.TCPServer):
    allow_reuse_address = True

httpd = MyServer(("", PORT), MyHandler)

print "go to http://localhost:%d"% PORT
httpd.serve_forever()
