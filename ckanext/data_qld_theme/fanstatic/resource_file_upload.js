jQuery(document).ready(function () {
  // if there is a validation error block on updating a resource, show the field nature_of_change, otherwise hide it by default
  if (jQuery('input[name="id"]').val().length > 0 && jQuery('#field-nature_of_change').parent().children('.error-block').length > 0) {
    jQuery('#field-nature_of_change').parent().parent().show();
  }
  else {
    jQuery('#field-nature_of_change').parent().parent().hide();
  }

  // Hide resource size element on loading of a resource edit form if the resource file was uploaded
  if (jQuery('.image-upload[data-module="image-upload"]').data('module-is_upload') == true) {
    jQuery('#field-size').parent().parent().hide();
  }
  // Show field-size element on loading of a resource edit form if the resource file was a url link
  else if (jQuery('.image-upload[data-module="image-upload"]').data('module-is_url') == true) {
    jQuery('#field-size').parent().parent().show();
  }

  // Hide the resource element if a file was selected to upload
  jQuery('#field-image-upload').change(function () {
    jQuery('#field-size').parent().parent().fadeOut();
    show_nature_of_change()
  });

  // Show the resource element if a url link was entered
  jQuery('#field-image-url').change(function () {
    jQuery('#field-size').parent().parent().fadeIn();
    show_nature_of_change()
  });

  // Insert field is required asterisk for labels 
  jQuery('.control-label[for="field-image-upload"]').parent().prepend('<span title="This field is required" class="control-required">*</span> ')
  jQuery('.control-label[for="field-image-url"]').parent().prepend('<span title="This field is required" class="control-required">*</span> ')
  jQuery('.control-label[for="field-nature_of_change"]').parent().prepend('<span title="This field is required" class="control-required">*</span> ')

  function show_nature_of_change() {
    // Only show nature of change when editing a resource 
    // id value will be null for new resource 
    if (jQuery('input[name="id"]').val().length > 0) {
      jQuery('#field-nature_of_change').val("");
      jQuery('#field-nature_of_change').parent().parent().show();
    }
  }
});