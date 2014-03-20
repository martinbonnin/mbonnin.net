var documentReady = function documentReady()
{
    $(".bubble").hover(
        function (o) {
            $(o.target).css("top", "0px");
        },
        function (o) {
            $(o.target).css("top", "-50px");
        });
    
    var hover = function hover(o, hoverIn) {
        if (hoverIn) {
            var opacity = 1;
            var top = "-15px";
        } else {
            var opacity = 0;
            var top = "0";
        }
        var v = $(o.target).closest(".vignette");
        v.find(".front").css("opacity", opacity);
        v.find(".vignette-thumbnail").css("top", top);
    }
    
    $(".home .front, .home .vignette-summary").hover(
        function (o) {
            hover(o, true);
        },
        function (o) {
            hover(o, false);
        });
    
    var displayed = false;
    $(".button").click(
        function(o) {
            var menu = $(".menu");
            var height = menu[0].scrollHeight + "px";
            if (displayed) {
                menu.animate({"height": "0"}, 300, "linear");
                displayed = false;
            } else {
                if (!height)
                    height = "auto";
                menu.animate({"height": height}, 300, "linear", function() {menu.css("height", "auto");});
                displayed = true;
            }
        });
    // remove underlines
    $("h1,h2").closest("a").addClass("no-underline");
}

$(document).ready(documentReady);
