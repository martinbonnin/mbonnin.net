import collections;
import re;
import utils;
from lxml import etree;

class Renderer:
    def __init__(self, image_cb):
        self.prefix = [];
        self.image_cb = image_cb;
        self.link_re = "\[([^\]]*)\]\(([^\)]*)\)";
        self.list_re = "([\*#]+) *(.*)";

    def process_special_line(self, fd, lines):
        line = lines[0].strip();
        
        if (line == ""):
            lines.popleft();
            return True;

        def found(m):
            lines.popleft();

        m = re.search(r"== *(.*) *==", line);
        if (m):
            fd.write("<h2>" + m.group(1) + "</h2>\n");
            found(m);
            return True;
        m = re.search("= *(.*) *=", line);
        if (m):
            fd.write("<h1>" + m.group(1) + "</h1>\n");
            found(m);
            return True;
        m = re.search("<!--more-->", line);
        if (m):
            found(m);
            return True;
        m = re.search("!" + self.link_re, line);
        if (m):
            img_url = self.image_cb(m.group(2), True);
            fd.write("<a href=\"" + img_url + "\"><img src=\"" + img_url + "\" alt=\"" + m.group(1) + "\"/></a>\n");
            found(m);
            return True;
        return False;

    def output_text(self, fd, text):
        # XXX: is this valid ?
        text = utils.escape(text);
        # start with a dummy char that is not the escape char
        result = "X";
        start = 0;
        while(True):            
            m = re.search(self.link_re, text[start:]);
            if (not m):
                result += text[start:];
                break;
            result += text[start:start + m.start()];
            url = self.image_cb(m.group(2));
            result += "<a href=\"" + url + "\">" + m.group(1) + "</a>"
            start += m.end();
        result = re.sub(r"[^\\]\*([^\* ]*[^\\])\*", r"<b>\1</b>", result);
        result = re.sub(r"[^\\]_([^_ ]*[^\\])_", r"<em>\1</em>", result);
        # unescape
        result = re.sub(r"\\(.)", r"\1", result);
        fd.write(result[1:]);
    
    # text migh contain some HTML
    def output_mixed_text(self, fd, text):
        start = 0;
        stack=[];
        html_start = 0;
        
        while(True):            
            m = re.search("<([^> ]*)[^>]*>", text[start:]);
            if (not m):
                if (len(stack) == 0):
                    self.output_text(fd, text[start:]);
                else:
                    print("unterminated HTML: " + text);
                return;
            tag = m.group(1);
            # print("found tag " + m.group(0) + ": " + tag);
            if (tag[0] == "/"):
                old_tag = stack.pop();
                if (old_tag != tag[1:]):
                    print("non-matching html tag: " + old_tag + "-" + tag[1:]);
                if (len(stack) == 0):
                    fd.write(text[html_start:start + m.end()]);
            elif (tag[-2] == "/"):
                # self closing tag
                pass;
            elif (re.match("!--", tag)):
                # comment
                pass;
            else:
                if (len(stack) == 0):
                    self.output_text(fd, text[start:m.start()]);
                    html_start = m.start();
                stack.append(tag);
            start += m.end();


    def process_code_block(self, fd, lines):
        line = lines[0];
        if (not re.match("     *(.*)", line)):
            return False;
        
        fd.write("<pre><code>\n");
        while (len(lines) > 0):
            line = lines[0];
            m = re.match("     *(.*)", line);
            if (not m):
                break;
            # we need to escape as code might contain '<' and other stuff
            fd.write(utils.escape(m.group(1)) + "\n");
            lines.popleft();
        fd.write("</code></pre>\n");
        return True;
                
    def process_list_block(self, fd, lines):
        if (not re.match(self.list_re, lines[0])):
            return False;

        while(len(lines) > 0):
            line = lines[0];
            m = re.match(self.list_re, line);
            if (len(self.prefix) == 0):
                cur_p = "";
            else:
                cur_p = self.prefix[-1];

            if (not m):
                go_down = len(self.prefix);
            else:
                next_p = m.group(1);
                go_down = len(cur_p) - len(next_p);

            while(go_down > 0):
                p = self.prefix.pop();
                if (p[-1] == "*"):
                    fd.write("</ul>\n");
                else:
                    fd.write("</ol>\n");
                go_down += -1;
            
            if (not m):
                return;
            
            if (len(next_p) > len(cur_p)):
                if (next_p[-1] == "*"):
                    fd.write("<ul>");
                else:
                    fd.write("<ol>");
                self.prefix.append(next_p);
            fd.write("<li>");
            self.output_mixed_text(fd, m.group(2));
            lines.popleft();
            while (len(lines) > 0):
                m = re.match("     *(.*)", lines[0]);
                if (not m):
                    break;
                fd.write("<br />");
                self.output_mixed_text(fd, m.group(1));
                lines.popleft();
            fd.write("</li>\n");

        return True;
            
    def process_paragraph(self, fd, lines):
        fd.write("<p>");
        ret="";
        while (len(lines) > 0):
            line = lines.popleft();
            if (line == ""):
                break;
            ret += line + "\n";
            
        self.output_mixed_text(fd, ret);
        fd.write("</p>\n");
        return True;

    def render(self, markup, fd):
        lines = collections.deque(markup.splitlines());        
        while (len(lines) > 0):
            if (self.process_code_block(fd, lines)):
                continue;
            if (self.process_special_line(fd, lines)):
                continue;
            if (self.process_list_block(fd, lines)):
                continue;
            if (self.process_paragraph(fd, lines)):
                continue;

# helper function
def render(markup, fd, image_cb):
    Renderer(image_cb).render(markup, fd);
    
