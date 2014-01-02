/* --------------------------------------------------------------------- */

var i = 0;
var makeText = function makeText(str)
{
    var text = $("<div>");

    text.css("font-family", "sans-serif");
    text.css("font-size", "18px");
    text.css("color", "#404040");
    text.text(str);
    text.attr("id", "text" + (i++));

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
    var base = "posts/" + p.directory + "/thumbnail_" + (odd ? "green":"yellow");
    
    thumbnail = makeHoverImage(base + "_bw.png", base + ".png", p.title);
    thumbnail.css("position", "absolute");
    thumbnail.css("width", 0.1 * width);
    thumbnail.css("height", 0.1 * width);
    thumbnail.css("left", odd * 0.05 * width);

    left.append(thumbnail);
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

    var title = makeText(p.title);
    var date_str = makeText(p.date_str);
    var description = makeText(p.description);

    title.load(function() {console.log("title loaded: " + title.height());});
    centerer.append(title);
    centerer.append(date_str);
    centerer.append(description);
    right.append(centerer);

    total_height = 18 * 3; //title.height() + date_str.height() + description.height();

    centerer.css("height", total_height);
    centerer.css("top", (right.height() - total_height)/2);
    vignette.append(right);

    return vignette;
}

var makeContent = function makeContent(centerer)
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

/* --------------------------------------------------------------------- */
