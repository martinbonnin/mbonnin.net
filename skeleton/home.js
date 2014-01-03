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

    return text;
}

var makeVignette = function makeVignette(p, index)
{
    var vignette = $("<div>");
    vignette.css("position", "relative");
    vignette.css("box-sizing", "border-box");
    vignette.attr("class", "vignette");
    vignette.css("width", "100%");
    vignette.css("padding-bottom", "18%");

    var left = $("<div>");
    left.attr("class", "left");
    left.css("position", "absolute");
    left.css("width", "30%");
    left.css("height", "100%");

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
    right.css("height", "100%");
    
    var table = $("<table>");
    table.css("width", "100%");
    table.css("height", "100%");
    right.append(table);
    var tr = $("<tr>");
    table.append(tr);
    var td = $("<td>").css("vertical-align", "middle");
    tr.append(td);
    
    var centerer = $("<div>");

    var title = makeText(p.title, 22);
    title.css("font-weight", "bold");
    centerer.attr("class", "centerer");
    centerer.css("width", "100%");
    centerer.css("margin", "auto");

    var date_str = makeText("" + p.date_str + "", 14);
    var description = makeText(p.description, 20);

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

    
    description.css("padding-top", "1em");
    centerer.append(a);
    centerer.append(date_str);
    centerer.append(description);
    td.append(centerer);
    right.append(table);

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

    return;
}

var getDepth = function getDepth() {
    return "";
}
/* --------------------------------------------------------------------- */
