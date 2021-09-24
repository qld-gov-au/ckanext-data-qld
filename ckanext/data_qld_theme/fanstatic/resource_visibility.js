jQuery(document).ready(function () {
    var $el = jQuery('#field-resource_visibility');
    $el.parents('form').submit(function () {
        $el.find('option').removeAttr('disabled');
    });
});
