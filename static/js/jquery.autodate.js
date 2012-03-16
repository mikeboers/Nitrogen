
(function($) {

var iso_format = 'yyyy-MM-dd HH:mm:ss';
var timezone_abbr = new Date().toString().split("(")[1].split(")")[0];
var timezone_offset = new Date().getTimezoneOffset() * 60 * 1000;

var defaults = {
    'displayFormat': 'dddd, MMMM d, yyyy, hh:mm:ss tt',
    'postFormat': iso_format
};

Date.CultureInfo.dateElementOrder = 'ymd';

$.autodate = function(elem, opts) {
    
    opts = $.extend({}, defaults, opts);
    
	// We create a hidden input which will contain the data that will
	// actually be sent back to the server. The visible input (whose
	// name is prefixed with "raw") is parsed on every change by the
	// date.js library, and sets the hidden input to something that
	// WTForms is expecting on the backend.
	
	// Wrap the visible input (which will be used for local time).
	var $local_input = $(elem);
	$local_input.wrap('<div class="autodate-wrapper" />');
	
	var $utc_input = $('<input type="hidden" />')
		.attr('name', $local_input.attr('name'))
		.insertAfter($local_input);
	
    // Convert the UTC from server into actual local time with timezone abbr.
    var local_time = Date.parseHuman($local_input.val() + 'UTC');
    if (local_time !== null) {
		var local_str = local_time.toString(iso_format);
    	$local_input.val(local_str + ' ' + timezone_abbr);
	}

	var raw_name = 'autodate-raw-' + $local_input.attr('name');
	$local_input.attr('name', raw_name).addClass('autodate')
	
	$label = $('<label class="autodate-label"/>')
		.attr('for', raw_name)
		.insertAfter($local_input);
	
	function _update()
	{
		var local_time = Date.parseHuman($local_input.val());
		var utc_time = local_time ? new Date(local_time.getTime() + timezone_offset) : null;
		
		$label.text(local_time ? local_time.toString(opts.displayFormat) + ' ' + timezone_abbr : 'INVALID DATE');
		$utc_input.val(utc_time ? utc_time.toString(opts.postFormat) : 'YYYY-MM-DD HH-MM-SS');
	}
	
	// Setup the date picker.
	$local_input.datepicker({
		showOn: 'button',
		buttonImage: '/img/silk/date.png',
		buttonImageOnly: true,
		showButtonPanel: true,
		changeMonth: true,
		changeYear: true,
		dateFormat: 'DD, MM d, yy',
		onClose: _update,
		showAnim: 'fadeIn',
		currentText: 'Goto Today'
	});
    
    _update()
	$local_input.keyup(_update);
}

$.fn.autodate = function(opts)
{
    $(this).each(function() {
        $.autodate(this, opts);
    })
}

})(jQuery);
