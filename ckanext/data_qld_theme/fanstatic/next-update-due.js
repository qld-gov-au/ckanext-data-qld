jQuery(document).ready(function () {

    UPDATE_FREQUENCY_DAYS = JSON.parse(jQuery('input[name="update_frequency_days"]').val())
    update_frequency_changed();

    jQuery("#field-update_frequency").change(function () {
        update_frequency_changed();
    });

    function update_frequency_changed() {
        let update_frequency = jQuery("#field-update_frequency :selected").val();
        if (update_frequency in UPDATE_FREQUENCY_DAYS) {
            jQuery("#field-next_update_due").parent().parent().show();
            // Check if required asterix is already shown to prevent duplicates
            if (jQuery('.control-label[for="field-next_update_due"').parent().children('span.control-required').length == 0) {
                jQuery('.control-label[for="field-next_update_due"').parent().prepend('<span title="This field is required" class="control-required">*</span> ')
            }
            due_date = recalculate_due_date(update_frequency);
            // convert the date format to apply the datepicker element
            next_update_due = moment(due_date).format('YYYY-MM-DD');
            jQuery("#field-next_update_due").val(next_update_due);
        }
        else {
            jQuery("#field-next_update_due").val("");
            jQuery("#field-next_update_due").parent().parent().hide();
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
