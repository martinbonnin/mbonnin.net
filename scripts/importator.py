#!/usr/bin/env python
# coding=utf8

from lxml import etree;
import sys;
import os;
import os.path;
import json;
import re;
import time;
import codecs;
import string;
import urlparse;
import utils;
import cgi;

def nicify(name):
    ret = name.lower()
    ret = re.sub(" ", "-", ret);
    ret = re.sub("é", "e", ret);
    ret = re.sub("'", "", ret);
    return ret;    
    
def _content(tag):
    return "{http://purl.org/rss/1.0/modules/content/}" + tag;

def _wp(tag):
    return "{http://wordpress.org/export/1.0/}" + tag;

class Post:
    def __init__(self, item):
        title = item.findtext("title");
        self.in_list = 0;
        print("processing " + title);
        
        date = time.strptime(item.findtext("pubDate"), "%a, %d %b %Y %H:%M:%S +0000");
        dirname = time.strftime("%Y-%m-%d_", date) + nicify(title); 
        post_dir = published_dir + "/" + dirname;
        try:
            os.mkdir(post_dir);
        except:
            pass;

        try:
            f = codecs.open(post_dir + "/page.mml", encoding='utf-8', mode="wb");
        except:
            print("cannot open file");
            raise;
        self.f = f;
        self.dir = post_dir;

    def write_header(self, item, tree):
        header = {};
        header['title'] = item.findtext("title");
        # XPath bullshit: selects the text of the sibling of meta_key element whose textContent is _thumbnail_id
        # I cannot use find() as it does not seem to recognize predicates like [.='foo']
        thumbnail_ids = item.xpath("*//*[local-name()='meta_key'][.='_thumbnail_id']/following-sibling::*/text()");
        if (thumbnail_ids):        
            #print("select thumbnail " + thumbnail_ids[0]);
            thumbnail_urls = tree.xpath("//*[local-name()='post_id'][.='" + thumbnail_ids[0] + "']/parent::*/*[local-name()='attachment_url']/text()");
            if (thumbnail_urls):
                ext = os.path.splitext(thumbnail_urls[0])[1].lower();
                proc = utils.execute_shell('wget -O ' + self.dir + '/thumbnail' + ext + ' ' + thumbnail_urls[0]);
                if (proc.returncode != 0):
                    print("cannot download " + thumbnail_urls[0]);
                    print(proc.err);
                    print(proc.out);
                header['thumbnail'] = os.path.basename(thumbnail_urls[0]);
                
        self.f.write(json.dumps(header, indent=4));
        self.f.write("\n\n");

    def transform_code_blocks(self, content):
        #we need a root node to have a valid XML document
        ret = "<xml>";
        lines = content.splitlines();
        current_code_tag = None;
        for line in lines:
            match = re.search("\[(/?)([^ \]]*).*", line);                
            if (match):
                m = match.group(2).lower();
                has_code_tag = ((m == "source") | (m == "sourcecode"));
                closing = match.group(1) == "/";
            else:
                has_code_tag = False;
                closing = False;

            if (current_code_tag):
                if (has_code_tag & closing):
                    if (m != current_code_tag):
                        print("got " + m + " instead of " + current_code_tag);
                    current_code_tag = None;
                    ret += "</code>";
                    continue;
            elif (has_code_tag & (not closing)):
                current_code_tag = match.group(2).lower();
                ret += "<code>";
                continue;

            if (current_code_tag):
                ret += cgi.escape(line) + "\n";
            else:
                ret += line + "\n";

        ret += "</xml>";
        return ret;

    def write_content(self, item):
        xml = self.transform_code_blocks(item.findtext(_content("encoded")));

        #print("----------------------------------------------------\n" + xml);
        # fromstring() fals on 'href="http://server/path?a=1&b=2
        #content = etree.fromstring(xml);
        content = etree.HTML(xml);
        self.prefix="";
        
        def unhandled(element):
            print("skipped " + element.tag + etree.tostring(element));

        def write_img(element):
            self.f.write("![" + element.get("alt") + "]");
            attachment = download_attachment(element.get("src"));
            if (not attachment):
                print("cannot download attachment " + element.get("src"));
                attachment = element.get("src");
            self.f.write("(" + attachment + ")");
            

        def download_attachment(attachment):
            if (string.find(attachment, "wp-content/upload") != -1):
                item_link = item.findtext("link");
                attachment = urlparse.urljoin(item_link, attachment);
                attachment_name = attachment[string.rfind(attachment, "/"):];
                af = self.dir + attachment_name;
                #print("download " + attachment + " to " + f);
                if (not os.path.isfile(af)):
                    print("downloading... " + attachment);
                    proc = utils.execute_shell('wget -O ' + af + ' ' + attachment);
                    if (proc.returncode != 0):
                        print("cannot download " + attachment);
                        print(proc.err);
                        os.remove(af);
                        sys.exit(2);
                return attachment_name[1:];

        def walk(element):
            for child in element.iterchildren():
                text = "";
                if (child.text):
                    text = child.text;
                if (isinstance(child.tag, basestring)):
                    if (child.tag == "ul"):
                        self.prefix += "*";
                        self.f.write("\n");
                        self.in_list += 1;
                        walk(child);
                        self.in_list -= 1;
                        self.prefix = self.prefix[:-1];
                        if (len(self.prefix) == 0):
                            self.f.write("\n");
                        continue;
                    elif (child.tag == "ol"):
                        self.prefix += "#";
                        self.in_list += 1;
                        walk(child);
                        self.in_list -= 1;
                        self.prefix = self.prefix[:-1];
                        if (len(self.prefix) == 0):
                            self.f.write("\n");
                        continue;
                    elif (child.tag == "li"):
                        # strip leading whitespace
                        while (len(text) and (text[0] == '\n' or text[0] == ' ')):
                            text = text[1:];
                        text = re.sub("\n", "\n    ", text);
                        self.f.write(self.prefix + " " + text);
                        # there might be <a> or <br> embedded inside <li>
                        walk(child);
                        self.f.write("\n");
                        continue;
                    elif (child.tag == "a"):
                        if (len(child) == 1 and child[0].tag == "img"):
                            write_img(child[0]);
                        elif (len(child) == 0):
                            href = child.get("href");
                            if (href):
                                self.f.write("[" + text + "]");
                                self.f.write("(" + href + ")");
                                download_attachment(href);
                            else:
                                unhandled(child);
                        else:
                            unhandled(child);
                    elif (child.tag == "img"):
                        if (len(child) == 0):
                            write_img(child);
                        else:
                            unhandled(child);
                    elif (child.tag == "br"):
                        pass;
                    elif (child.tag == "p"):
                        self.f.write(text);
                        walk(child);
                    elif (child.tag == "body"):
                        # it seems this tag is generated automatically
                        walk(child);
                    elif (child.tag == "xml"):
                        # this tag we put it 
                        self.f.write(text);
                        walk(child);
                    elif (child.tag == "h1"):
                        if (len(child) == 0):
                            self.f.write("= " + text + " =\n");
                        else:
                            unhandled(child);
                    elif (child.tag == "h3"):
                        if (len(child) == 0):
                            self.f.write("== " + text + " ==\n");
                        else:
                            unhandled(child);
                    elif (child.tag == "code"):
                        if (len(child) == 0):                            
                            lines = text.split("\n");
                            for line in lines:
                                self.f.write("    " + utils.unescape(line) + "\n");
                        else:
                            unhandled(child);
                    else:
                        self.f.write("<" + child.tag);
                        for key in child.keys():
                            self.f.write(" " + key + "=\"" + cgi.escape(child.get(key)) + "\"");
                        self.f.write(">");
                        self.f.write(text);
                        walk(child);
                        self.f.write("</" + child.tag + ">");
                elif (isinstance(child, etree._Comment)):
                    self.f.write(etree.tostring(child));

                if (child.tail):
                    if (self.in_list):
                        tail = re.sub("\n", "\n    ", child.tail);
                    else:
                        tail = child.tail;
                    self.f.write(tail);
                
        walk(content);

#
# main program
#
if (len(sys.argv) < 3):
    print("usage: " + sys.argv[0] + " [wordpress file] [directory]");
    sys.exit(2);

wxr = sys.argv[1];
out_dir = sys.argv[2];
published_dir = out_dir + "/published";

try:
    os.makedirs(out_dir);
except:
    pass;

try:
    os.mkdir(published_dir);
except:
    pass;

print("wxr=" + wxr);
print("out_dir=" + out_dir);


tree = etree.parse(wxr);

config = {};
config['title'] = tree.findtext("/channel/title");
config['description'] = tree.findtext("/channel/description");

config_file = open(out_dir + "/blog_parameters.json", "wb");
config_file.write(json.dumps(config, indent=4));

items = tree.findall("/channel/item");
for item in items:
    if (item.findtext(_wp("post_type")) == "post"):
        post = Post(item);
        post.write_header(item, tree);
        post.write_content(item);
        
print("done");
#print etree.tostring(tree);


