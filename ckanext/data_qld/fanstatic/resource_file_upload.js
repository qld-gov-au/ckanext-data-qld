jQuery(document).ready(function () {
  UPDATE_FREQUENCY_DAYS = JSON.parse(jQuery('input[name="update_frequency_days"]').val())
  UPDATE_FREQUENCY = jQuery('input[name="update_frequency"]').val()

  // if there is a validation error block on updating a resource, show the field nature_of_change, otherwise hide it by default
  if (jQuery('input[name="id"]').val().length > 0 && jQuery('#field-nature_of_change').parent().children('.error-block').length > 0) {
    jQuery('#field-nature_of_change').parent().parent().show();
  }
  else {
    jQuery('#field-nature_of_change').parent().parent().hide();
  }

  // Hide resource size element on loading of a resource edit form if the resource file was uploaded
  if (jQuery('#resource-url-upload').prop('checked') === true) {
    jQuery('#field-size').parent().parent().hide();
  }
  // Show field-size element on loading of a resource edit form if the resource file was a url link
  else {
    jQuery('#field-size').parent().parent().show();
  }

  // Hide the resource element if a file was selected to upload
  jQuery('#field-resource-upload').change(function () {
    jQuery('#field-size').parent().parent().fadeOut();
    show_nature_of_change()
  });

  // Show the resource element if a url link was entered
  jQuery('#field-resource-url').change(function () {
    jQuery('#field-size').parent().parent().fadeIn();
    show_nature_of_change()
  });

  // Insert field is required asterisk for labels
  jQuery('.control-label[for="field-resource-upload"]').parent().prepend('<span title="This field is required" class="control-required">*</span> ')
  jQuery('.control-label[for="field-resource-url"]').parent().prepend('<span title="This field is required" class="control-required">*</span> ')
  jQuery('.control-label[for="field-nature_of_change"]').parent().prepend('<span title="This field is required" class="control-required">*</span> ')

  function show_nature_of_change() {
    // Only show nature of change when editing a resource
    // id value will be null for new resource
    // Dont show the field if the update_frequency for dataset is not in defined values
    if (jQuery('input[name="id"]').val().length > 0 && UPDATE_FREQUENCY in UPDATE_FREQUENCY_DAYS) {
      jQuery('#field-nature_of_change').val("");
      jQuery('#field-nature_of_change').parent().parent().show();
    }
  }
});
