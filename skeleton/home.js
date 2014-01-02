/* --------------------------------------------------------------------- */

var i = 0;
var makeText = function makeText(str, fontSize)
{
    var text = $("<div>");

    if (!fontSize) {
        fontSize = 18;
    }
    
    text.css("font-size", fontSize + "px");
    text.text(str);
    text.attr("id", "text" + (i++));
    text.css("position", "absolute");    

    // HACK to measure the height of the text
    // height is not valid until the node has been added somewhere in the DOM...
    text.attr("visibility", "hidden");
    $("body").append(text);
    text.height2 = text.height();
    text.attr("visibility", "");
    text.remove();
    return text;
}

var makeVignette = function makeVignette(p, index)
{
    var vignette = $("<div>");
    vignette.css("position", "absolute");
    vignette.attr("class", "vignette");
    vignette.css("width", "100%");
    vignette.css("height", 0.1 * width);

    var left = $("<div>");
    left.attr("class", "left");
    left.css("position", "absolute");
    left.css("width", "30%");
    left.css("height", 0.1 * width);

    var odd = (index >> 0) % 2;
    var base = p.path + "/thumbnail_" + (odd ? "green":"yellow");
    
    var thumbnail = makeHoverImage(base + "_bw.png", base + ".png", p.title);
    thumbnail.css("position", "absolute");
    thumbnail.css("width", 0.1 * width);
    thumbnail.css("height", 0.1 * width);
    thumbnail.css("left", odd * 0.05 * width);
    thumbnail.front.css("transition", "opacity 0.5s");

    var a = $("<a>");
    a.append(thumbnail);
    a.attr("href", "" + p.path);

    left.append(a);
    vignette.append(left);

    var right = $("<div>");
    right.attr("class", "right");
    right.css("position", "absolute");
    right.css("width", "70%");
    right.css("left", "30%");
    right.css("height", 0.1 * width);

    var centerer = $("<div>");
    centerer.attr("class", "centerer");
    centerer.css("position", "absolute");
    centerer.css("width", "100%");

    var title = makeText(p.title, 18);
    title.css("font-weight", "bold");

    var y =  title.height2;
    var date_str = makeText("" + p.date_str + "", 10);
    date_str.css("top", y);
    y += 1.7 * date_str.height2;
    var description = makeText(p.description, 16);
    description.css("top", y);
    y += description.height2;

    var a = $("<a>");
    a.append(title);
    a.attr("href", "" + p.path);
    a.css("text-decoration", "none");
    a.hover(function () {
            thumbnail.front.css("opacity", 1);
            title.css("color", "#009000");
        },
        function () {
            thumbnail.front.css("opacity", 0);
            title.css("color", "#404040");
        });

    
    centerer.append(a);
    centerer.append(date_str);
    centerer.append(description);
    right.append(centerer);

    total_height = y;

    centerer.css("height", total_height);
    centerer.css("top", (right.height() - total_height)/2);
    vignette.append(right);

    return vignette;
}

var getContent = function getContent(centerer)
{
    var y = 0;
    var spacing = 0.01 * width;
    
    for (i in posts) {
        var vignette = makeVignette(posts[i], i);
        vignette.css("top", y);
        centerer.append(vignette);
        y += vignette.height() + spacing;
    }
    
    y -= spacing;
    centerer.css("height", y);

    return;
}

var getDepth = function getDepth() {
    return "";
}
/* --------------------------------------------------------------------- */
