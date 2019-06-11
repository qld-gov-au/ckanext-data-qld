jQuery(document).ready(function() {

  jQuery('input[name="upload"]').change(function() {
    jQuery('#field-size').parent().parent().fadeOut();
  });

  jQuery('input[name="url"]').change(function() {
    jQuery('#field-size').parent().parent().fadeIn();
  });

});