/* --------------------------------------------------------------------- */

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
