jQuery(document).ready(function() {

    jQuery('.flag-comment').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var elem = jQuery(this);
        var comment_id = jQuery(this).data('comment-id');
        jQuery.get('/comment/' + comment_id + '/flag', function() {
            elem.addClass('hidden');
            elem.off('click');
            elem.parent().find('.comment-flagged').removeClass('hidden');
            alert("This comment has been flagged for inappropriate content");
        })
        .fail(function() {
            alert("An error occurred while attempting to flag this comment");
        });
        return false;
    });

});