
(function($) {

var defaults = {
    'displayFormat': 'dddd, MMMM d, yyyy, hh:mm:ss tt',
    'postFormat': 'yyyy-MM-dd HH:mm:ss',
}
$.autodate = function(elem, opts) {
    
    opts = $.extend({}, defaults, opts);
    
	// We create a hidden input which will contain the data that will
	// actually be sent back to the server. The visible input (whose
	// name is prefixed with "raw") is parsed on every change by the
	// date.js library, and sets the hidden input to something that
	// formalchemy is expecting on the backend.
	var $input = $(elem);
	$input.wrap('<div class="autodate-wrapper" />');
	var $hidden = $('<input type="hidden" />')
		.attr('name', $input.attr('name'))
		.insertAfter($input);
	var raw_name = 'autodate-raw-' + $input.attr('name');
	$input.attr('name', raw_name).addClass('autodate')
	$label = $('<label class="autodate-label"/>')
		.attr('for', raw_name)
		.insertAfter($input);
	
	function _update()
	{
		var date = Date.parse($input.val());
		$label.text(date ? date.toString(opts.displayFormat) : 'INVALID DATE');
		$hidden.val(date ? date.toString(opts.postFormat) : 'YYYY-MM-DD HH-MM-SS');
	}
	
	// Setup the date picker.
	$input.datepicker({
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
	
	_update();
	$input.keyup(_update);
}

$.fn.autodate = function(opts)
{
    $(this).each(function() {
        $.autodate(this, opts);
    })
}

})(jQuery);