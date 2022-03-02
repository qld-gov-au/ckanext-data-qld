jQuery(document).ready(function () {

    UPDATE_FREQUENCY_DAYS = JSON.parse(jQuery('input[name="update_frequency_days"]').val())
    update_frequency_changed();

    jQuery("#field-update_frequency").change(function () {
        update_frequency_changed(true);
    });

    function update_frequency_changed(change_event) {
        let update_frequency = jQuery("#field-update_frequency :selected");
        let control_label = jQuery('.control-label[for="field-next_update_due"]').parent();
        let next_update_due_field = jQuery("#field-next_update_due");
        if (update_frequency.val() in UPDATE_FREQUENCY_DAYS) {
            next_update_due_field.parent().parent().show();
            // Check if required asterix is already shown to prevent duplicates
            if (control_label.children('span.control-required').length == 0) {
                control_label.prepend('<span title="This field is required" class="control-required">*</span> ')
            }
            if (change_event) {
                due_date = recalculate_due_date(update_frequency.val());
                // convert the date format to apply the datepicker element
                next_update_due = moment(due_date).format('YYYY-MM-DD');
                next_update_due_field.val(next_update_due);
            }
        }
        else {
            next_update_due_field.val("");
            next_update_due_field.parent().parent().hide();
        }
    };

    // Add update frequencies days to todays date
    function recalculate_due_date(update_frequency) {
        var today = new Date();
        var days = UPDATE_FREQUENCY_DAYS[update_frequency]
        due_date = today.setDate(today.getDate() + days);
        return due_date;
    };

});
