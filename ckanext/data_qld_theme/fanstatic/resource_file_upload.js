jQuery(document).ready(function () {

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
  });

  // Show the resource element if a url link was entered
  jQuery('#field-image-url').change(function () {
    jQuery('#field-size').parent().parent().fadeIn();
  });

  // Insert field is required asterisk for labels 
  jQuery('.control-label[for="field-image-upload"').parent().prepend('<span title="This field is required" class="control-required">*</span> ')
  jQuery('.control-label[for="field-image-url"').parent().prepend('<span title="This field is required" class="control-required">*</span> ')

});