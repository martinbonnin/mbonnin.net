
var blog_parameters = {
    "description": "breaking and fixing", 
    "title": "mbonnin's blog",
}

var width;

var makeHoverImage = function makeHoverImage(src_back, src_front, title)
{
    var hoverImage = $("<div>");

    var makeImage = function makeImage(src) {
        var img = $("<img>");
        img.attr("src", src);
        img.attr("alt", title);
        img.attr("title", title);
        img.css("position", "absolute");
        img.css("width", "100%");
        img.css("max-height", "100%");
        img.css("max-width", "100%");
        return img;
    }

    var back = hoverImage.back = makeImage(src_back);
    var front = hoverImage.front = makeImage(src_front);
    
    front.css("z-index", 1);
    front.css("opacity", 0);
    //front.css("transition", "opacity 1s");
    
    hoverImage.hover(
        function () {
            front.css("opacity", 1);
        },
        function () {
            front.css("opacity", 0);
        });
    
    hoverImage.append(back);
    hoverImage.append(front);

    return hoverImage;
}

var makeHeader = function makeHeader()
{
    var header = $("<div>");
    var w = width;
    var h = 0.1 * width;
    var padding = 0.20 * h;
    var sha
    
    header.css("background", "#000000");
    header.css("position", "absolute");
    header.css("width", w);
    header.css("height", h);
    header.css("box-shadow", "0 0 " + (0.02 * h) + "px " + (0.02 * h) + "px rgba(0,0,0,0.5)");
    
    var title_logo = $("<img>");
    title_logo.attr("src", "res/title_logo.png");
    title_logo.css("position", "absolute");
    title_logo.css("width", 0.33 * w);
    title_logo.css("top", 0.10 * h);
    title_logo.css("left", padding);
    header.append(title_logo);
    
    var bubble_size = 0.27 * h;
    var appendBubble = function(what, href, x) {
        var a = $("<a>");
        a.attr("href", href);
        var src_base = "res/bubble_" + what;
        var bubble = makeHoverImage(src_base + "_bw.png", src_base + ".png", what);
        bubble.css("position", "absolute");
        bubble.css("width", bubble_size);
        bubble.css("height", bubble_size);
        bubble.css("top", 0.40 * h);
        bubble.css("left", x);
        a.append(bubble);
        header.append(a);
    }

    var bubble_spacing = 0.08 * h;
    var x = w - bubble_size - padding;
    appendBubble("about", "about.html", x);
    x -= bubble_size + bubble_spacing;
    appendBubble("rss", "feed/", x);
    x -= bubble_size + bubble_spacing;
    appendBubble("linkedin", "http://www.linkedin.com/pub/martin-bonnin/1/344/947", x);
    x -= bubble_size + bubble_spacing;
    appendBubble("github", "https://github.com/martinbonnin", x);

    return header;
}
  
var makeFooter = function makeFooter()
{
    var footer = $("<div>");
    var w = width;
    var h = 0.02 * width;
    
    footer.css("background", "#000000");
    footer.css("position", "absolute");
    footer.css("width", w);
    footer.css("height", h);
    footer.css("box-shadow", "");
    return footer;
}

var documentReady = function documentReady()
{
    var y = 0;
    $("head").append($("<title>").text(blog_parameters["title"] + " | " + blog_parameters["description"]));
    
    $("body").css("background", "#e9e9e9");
    $("body").css("margin", "0");
    $("body").css("padding", "0");

    // force a scrollbar on the right so that we get the correct width
    $("body").css("overflow-y", "scroll");
    width = $(document).width();

    var header = makeHeader();
    header.css("top", y);
    $("body").append(header);    
    y += header.height();
    
    var centerer = $("<div>");
    var padding_v = 0.035 * width;
    var padding_h = 0.10 * width;
    centerer.css("position", "absolute");
    centerer.css("top", y + padding_v);
    centerer.css("left", padding_h);
    centerer.css("width", width - 2 * padding_h);

    makeContent(centerer);

    $("body").append(centerer);
    y += centerer.height() + 2 * padding_v;

    var footer = makeFooter();
    footer.css("top", y);
    $("body").append(footer);
}

$(document).ready(documentReady);
