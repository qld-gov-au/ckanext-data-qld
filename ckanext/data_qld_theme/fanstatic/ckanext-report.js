jQuery(document).ready(function () {
    // This will trigger a form submit from any organisation drop down change from any reports registered with ckanext-report
    jQuery(".js-auto-submit").change(function () {
        jQuery(this).closest("form").submit();
    });
});
