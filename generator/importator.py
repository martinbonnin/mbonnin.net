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
import HTMLParser;
import string;
import urlparse;
import utils;

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
        print("processing " + title);
        
        date = time.strptime(item.findtext("pubDate"), "%a, %d %b %Y %H:%M:%S +0000");
        dirname = time.strftime("%Y-%m-%d_", date) + nicify(title); 
        post_dir = published_dir + "/" + dirname;
        try:
            os.mkdir(post_dir);
        except:
            pass;

        try:
            f = codecs.open(post_dir + "/page.markdown", encoding='utf-8', mode="wb");
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
                header['thumbnail'] = os.path.basename(thumbnail_urls[0]);
                
        self.f.write(json.dumps(header, indent=4));
        self.f.write("\n\n");

    def write_content(self, item):

        lines = item.findtext(_content("encoded")).splitlines();
        item_link = item.findtext("link");

        current_code_tag = None;
        list_stack = [];
        line_is_first = 0;
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
                else:
                    # XXX: should I unescape ?
                    line = HTMLParser.HTMLParser().unescape(line);
                    self.f.write("    " + line + "\n");
                continue;
            elif (has_code_tag & (not closing)):
                current_code_tag = match.group(2).lower();
                continue;

            # XXX: not very nice.... should it use a html parser ?
            if (re.search("<ul[^>]*>", line)):
                #print("<ul>");
                list_stack.append({"tag": "ul"});
                line_is_first = 0;
                continue;
            elif (re.search("<ol[^>]*>", line)):
                #print("<ol>");
                list_stack.append({"tag": "ol"});
                line_is_first = 0;
                continue;
            elif (re.search("</ul>", line)):
                #print("</ul>");
                old = list_stack.pop();
                if (old['tag'] != "ul"):
                    print("got </ul> while expecting " + old['tag']);
                continue;
            elif (re.search("</ol*>", line)):
                #print("</ol>");
                old = list_stack.pop();
                if (old['tag'] != "ol"):
                    print("got </ol> while expecting " + old['tag']);
                continue;


            
            if (len(list_stack) > 0):
                #print(line)
                if (line_is_first):
                    list_stack[-1]['line'] = 0;
                    line_is_first = 0;
                elif (re.search("<li[^>]*>", line)):
                    list_stack[-1]['line'] = 0;
                    line = re.sub("[ \t]*<li[^>]*>.*", "", line);
                    if (line == ""):
                        #print("empty li");
                        line_is_first = 1;
                        continue;            
                else:
                    list_stack[-1]['line'] = list_stack[-1]['line'] + 1;

                if (list_stack[-1]['line'] > 0):
                    i = 0;
                    while (i < len(list_stack)):
                        self.f.write(" ");
                        i = i + 1;
                else:
                    for l in list_stack:
                        if (l['tag'] == "ul"):
                            self.f.write("*");
                        elif (l['tag'] == "ol"):
                            self.f.write("#");            
                self.f.write(" ");

            line = re.sub("</li>", "", line);
            line = re.sub("<br>", "", line);
            line = re.sub("<p>", "", line);
            line = re.sub("</p>", "", line);
            line = re.sub(r'<h1[^>]*>(.*)</h1>', r'= \1 =', line);
            line = re.sub(r'<h3[^>]*>(.*)</h3>', r'== \1 ==', line);
            a_re = r'<a.*href=[\'"]?([^\'"]*)[\'"]?[^>]*>(.*)</a>';
            while (1):
                match = re.search(a_re, line);
                if (not match):
                    break;
                attachment = match.group(1);
                attachment_name = None;
                if (string.find(attachment, "wp-content/upload") != -1):
                    attachment = urlparse.urljoin(item_link, attachment);
                    attachment_name = attachment[string.rfind(attachment, "/"):];
                    af = self.dir + attachment_name;
                    #print("download " + attachment + " to " + f);
                    if (not os.path.isfile(af)):
                        print("downloading... " + attachment);
                        proc = utils.Popen('wget -O ' + af + ' ' + attachment);
                        if (proc.returncode != 0):
                            print("cannot download " + attachment);
                            print(proc.err);
                            os.remove(af);
                            sys.exit(2);
                if (attachment_name):
                    line = re.sub(a_re, r'[\2](' + attachment_name[1:] + ')', line);
                else:
                    line = re.sub(a_re, r'[\2](\1)', line);

            line = re.sub(r'\[<img.*alt="([^"]*)".*/>\]', r'![\1]', line);
            self.f.write(line + "\n");

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


