jQuery(document).ready(function () {
    var dataset_delete_button = jQuery('#dataset-delete-button')
    original_href = dataset_delete_button.attr('href')
    dataset_delete_button.removeAttr('disabled')
    
    jQuery('body').on('keyup', '#deletion-reason', function (event) {
        var value = jQuery(event.target).val().trim();
        var btn_primary = jQuery('#modal-deletion-reason').find('.modal-footer .btn-primary')
        if (value.length >= 10) {
            new_href = original_href.concat('&deletion_reason=', value)
            dataset_delete_button.attr('href', new_href);
            btn_primary.removeAttr('disabled');
        } else {
            btn_primary.attr('disabled', 'disabled');
        }
    });
});