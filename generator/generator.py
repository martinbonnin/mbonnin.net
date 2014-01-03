#!/usr/bin/env python
import sys;
sys.dont_write_bytecode = True
import content;
import os;
import codecs;
import os.path;
import json;
import utils;
import imgutils;
import collections;
import re;
import time;
import urlparse;
from xml.sax.saxutils import escape

feed_header = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
	xmlns:content="http://purl.org/rss/1.0/modules/content/"
	xmlns:wfw="http://wellformedweb.org/CommentAPI/"
	xmlns:dc="http://purl.org/dc/elements/1.1/"
	xmlns:atom="http://www.w3.org/2005/Atom"
	xmlns:sy="http://purl.org/rss/1.0/modules/syndication/"
	xmlns:slash="http://purl.org/rss/1.0/modules/slash/"
	>

<channel>
	<title>mbonnin&#039;s blog</title>
	<atom:link href="%DOMAINfeed/" rel="self" type="application/rss+xml" />
	<link>%DOMAIN</link>
	<description>rabbits, computer science and the meaning of life</description>
	<lastBuildDate>%BUILDDATE</lastBuildDate>
	<language>en</language>
	<sy:updatePeriod>hourly</sy:updatePeriod>
	<sy:updateFrequency>1</sy:updateFrequency>
	<generator>mouahahahha</generator>""";

feed_footer = """</channel>
</rss>""";

feed_item =""" 		<item>
		<title>%TITLE</title>
		<link>%DOMAIN%PATH/</link>
		<pubDate>%PUBDATE</pubDate>
		<dc:creator>martin</dc:creator>
        <category><![CDATA[Uncategorized]]></category>

		<guid isPermaLink="true">%DOMAIN%PATH/</guid>
		<description>%DESCRIPTION</description>
			<content:encoded>%CONTENT_ENCODED</content:encoded>
		<slash:comments>0</slash:comments>
		</item>""";

feed_time_format = "%a, %d %b %Y %H:%M:%S +0000";
domain = "http://staging.mbonnin.net/";

class Generator:
    def __init__(self):
        pass;                

    def generate_content(self, directory):
        in_path = self.in_base_path + "/" + directory;
        out_path = self.out_base_path + "/" + directory;

        # parse content
        for d in os.listdir(in_path):
            if (not os.path.isdir(in_path + "/" + d)):
                continue;

            print("=== " + directory + "/" + d + "===");
            c = content.Content(self.in_base_path, in_path + "/" + d, out_path);
            c.path = directory + "/" + c.directory;
            getattr(self, directory).append(c);
        
    def generate_feed(self):
        feed_path = self.out_base_path + "/feed";
        try:
            os.makedirs(feed_path);
        except:
            #fatal("cannot make dir");
            pass;

        feed_path += "/index.html";
        fd = utils.open_file(feed_path, "wb");
        a = feed_header.replace("%BUILDDATE", time.strftime(feed_time_format, time.gmtime()));
        a = a.replace("%DOMAIN", domain);
        fd.write(a);
        for p in self.posts:
            a = feed_item;
            a = a.replace("%TITLE", escape(p.title));
            a = a.replace("%PUBDATE", time.strftime(feed_time_format, p.date));
            a = a.replace("%PATH", p.path);
            a = a.replace("%DESCRIPTION", escape(p.description));
            def make_absolute_url(m):
                #print("make absolute " + m.group(1));
                if (m.group(1).find("http:") == 0):
                    r = m.group(1);
                else:
                    r = urlparse.urljoin(domain + p.path + "/", m.group(1));
                #print("    => " + r);
                return "src=\"" + r + "\"";
            b = utils.re_replace_all('src="([^"]*)"', p.html, make_absolute_url);
            b = utils.re_replace_all('href="([^"]*)"', b, make_absolute_url);
            a = a.replace("%CONTENT_ENCODED", "<![CDATA[" + b + "]]>");
            a = a.replace("%DOMAIN", domain);
            fd.write(a);
        fd.write(feed_footer);
        
    def generate_home(self):
        # sort posts, in reverse order: latest first
        self.posts.sort(cmp=lambda x,y: cmp(y.date, x.date));

        # write the home app.js. It is the concatenation of:
        #  1. json dump of all posts
        #  2. page specific javascript
        #  3. common javascript
        home_fd = utils.open_file(self.in_base_path + "/home.js", "rb");
        common_fd = utils.open_file(self.in_base_path + "/common.js", "rb");
        app_fd = utils.open_file(self.out_base_path + "/app.js", "wb");

        app_fd.write("posts = ");
        posts = [{k: getattr(p, k, None) for k in ["path", "title", "date_str", "description"]} for p in self.posts];
        json.dump(posts, app_fd, indent=4);
        app_fd.write(";\n");
        app_fd.write(home_fd.read());
        app_fd.write(common_fd.read());
        utils.generate_index("mbonnin's blog", "", self.out_base_path + "/index.html");

    def generate(self, in_base_path, out_base_path):
        self.in_base_path = in_base_path;
        self.out_base_path = out_base_path;
        
        try:
            os.mkdir(out_base_path);
        except:
            pass;
                
        imgutils.init(in_base_path);
        utils.init(in_base_path);

        # copy static content
        utils.Popen("cp -rf " + in_base_path + "/res " + out_base_path);
         
        # 'dynamic' content
        for c in ["pages", "posts"]:
            setattr(self, c, []);
            self.generate_content(c);
        
        # home page
        self.generate_home();
        
        # feed
        self.generate_feed();
        
if(__name__ == "__main__"):
    if (len(sys.argv) < 3):
        print("usage: " + sys.argv[0] + " [input dir] [output dir]");
        sys.exit(1);

    Generator().generate(sys.argv[1], sys.argv[2]);


