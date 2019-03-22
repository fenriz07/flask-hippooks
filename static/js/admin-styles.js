function filterFormat(ul) {
    $(function() {
        $(ul).children("li").each(function() {
            var href = window.location.href;
            var query = $(this).text().toLowerCase()+"=True";
            if (href.indexOf(query) > -1) {
                $(ul).children("li").removeClass("active");
                $(this).addClass("active");
            }
        });
    });
}

function sortButtonMacro() {
    $(function() {
        $(".sort-button-toggle").each(function() {
            var href = window.location.href;
            var query = $(this).attr("href");
            if (href.indexOf(query) > -1) {
                $(this).addClass("is-sorted")
                .css("display", "none");
                $(this).siblings().addClass("is-sorted")
                .css("display", "inline");
            }
        });
    });
}
function tableHeightMatchSidebar() {
    $(function() {
        var sideBarHeight = $(".hipcooks-side").outerHeight() + "px";
        $(".hipcooks-data").css("min-height", sideBarHeight);
    });
}
