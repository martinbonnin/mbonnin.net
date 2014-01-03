
var blog_parameters = {
    "description": "rabbits, computer science and the meaning of life", 
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
    header.css("width", "100%");
    header.css("box-sizing", "border-box");
    header.css("padding-bottom", "10%");
    header.css("position", "relative");
    header.css("box-shadow", "0 0 " + (0.02 * h) + "px " + (0.02 * h) + "px rgba(0,0,0,0.5)");
    
    var title_logo = $("<img>");
    title_logo.attr("src", getDepth() + "res/title_logo.png");
    title_logo.css("position", "absolute");
    title_logo.css("width", "33%");
    title_logo.css("top", 0.10 * h);
    title_logo.css("left", padding);
    var a = $("<a>");
    a.attr("href", getDepth() + ".");
    a.append(title_logo);
    header.append(a);
    
    var bubble_size = 0.27 * h;
    var appendBubble = function(what, href, x) {
        var a = $("<a>");
        a.attr("href", href);
        var src_base = getDepth() + "res/bubble_" + what;
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
    appendBubble("about", getDepth() + "pages/about/", x);
    x -= bubble_size + bubble_spacing;
    appendBubble("rss", getDepth() + "feed/", x);
    x -= bubble_size + bubble_spacing;
    appendBubble("linkedin", "http://www.linkedin.com/pub/martin-bonnin/1/344/947", x);
    x -= bubble_size + bubble_spacing;
    appendBubble("github", "https://github.com/martinbonnin", x);

    return header;
}
  
var makeFooter = function makeFooter()
{
    var footer = $("<div>");
    
    footer.css("background", "#000000");
    footer.css("position", "relative");
    footer.css("width", "100%");
    footer.css("padding-bottom", "2%");
    footer.css("box-sizing", "border-box");
    return footer;
}

var documentReady = function documentReady()
{
    $("html").css("height", "100%");
    $("body").css("background", "#e9e9e9");
    $("body").css("margin", "0");
    $("body").css("padding", "0");
    $("body").css("height", "100%");

    // force a scrollbar on the right so that we get the correct width
    $("body").css("overflow-y", "scroll");
    width = $(document).width();

    var wrapper = $("<div>");
    wrapper.css("min-height", "100%");
    wrapper.attr("id", "wrapper");
    $("body").append(wrapper);

    var header = makeHeader();
    wrapper.append(header);    
    
    var centerer = $("<div>");
    var padding_v = 0.035 * width;
    var padding_h = 0.20 * width;
    centerer.css("position", "relative");
    centerer.attr("id", "content");
    centerer.css("padding", "3.5% 20%");
    centerer.css("min-height", "100%");

    getContent(centerer);

    wrapper.append(centerer);
    var footer = makeFooter();
    footer.css("position", "relative");
    footer.css("margin-top", "-2%");
    $("body").append(footer);
}

var measureHeight = function measureHeight(htmlStr, width)
{
    var div = $("<div>");
    div.css("position", "absolute");
    div.css("width", width);
    div.html(htmlStr);

    div.attr("visibility", "hidden");
    $("body").append(div);
    var h = div.height();
    div.attr("visibility", "");
    div.remove();
    return h;
}

$(document).ready(documentReady);
