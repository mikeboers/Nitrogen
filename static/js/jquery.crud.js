/*

This is the editable plugin for Mike Boers' nitrogen web framework.

Requirments:

    jquery-ui
    jquery.blockUI.js
    
    
*/

(function($){

$.crud = {};

$.crud.defaults = {
	deleteable: true,
	
	// Extra data to send along with the API request.
	// Useful for when you need more info for an API mdoel adapter callback.
	extraData: {}
}


$.fn.crud = function main(opts) { 
	
	if (this.length > 1)
	{
	    this.each(function(){ main.call(this, opts) });
	    return this;
	}
    
    var $$ = this;
	
	opts = $.extend({}, $.crud.defaults, opts);
	
	// To hold the markup that is removed when the form is deployed.
	var $form;
	var $children;
	var initial_data;
	
	function _init()
	{
	    $$.addClass('crud');
	    $$.removeClass('crud-active');
	    
		$children = $$.children();
		var $buttons = $('<div class="outer-buttons" />')
		    .appendTo($$);
		
		// Add the edit button.
		if (opts.id) {
			$('<a class="edit-button">Edit</a>')
			    .button()
			    .click(_start_edit)
			    .appendTo($buttons);
		}
		
		if (opts.id && opts.deleteable)
		{
			$('<a class="delete-button">Delete</a>')
			    .button()
			    .click(_delete_click_handler)
			    .appendTo($buttons);
		}
	}

	function _start_edit()
	{
		// Block out the UI while we get the form.
		$$.block({
			message: 'Retrieving form. Please wait...'
		});
        
		// Get the form.
		var data = $.extend({}, opts, opts.extraData, {
			method: 'get_form',
			id: opts.id ? opts.id : 0
		});
		
		$.ajax({
		    type: "POST",
		    url: opts.url,
		    data: data,
		    success: _build_form,
		    error: function() {
		        $$.unblock();
		        alert('There was an error while contacting the server.');
		    },
		    dataType: 'json'
		});
	}
	
	function _build_form(res)
	{
		// Unblock the UI, strip all the children, place the form.
		$$.unblock();
		$$.empty();
		$$.addClass('crud-active');
		
		var $wrapper = $('<div class="wrapper" />').appendTo($$);
		$form = $('<form />').appendTo($wrapper);
		$form.html(res.form);
		
		var buttons = $('<div class="inner-buttons" />')
			.appendTo($form);
		
		// Add the buttons.
		
        $('<a class="commit-button">Preview</a>')
            .button({'disabled': true})
            .appendTo(buttons)
		    // .click(_commit_click_handler);
        
		$('<a class="save-button">Save</a>')
		    .button()
		    .appendTo(buttons)
		    .click(_save_click_handler);
        $('<a class="cancel-button">Cancel</a>')
            .button()
            .appendTo(buttons)
            .click(_cancel_click_handler);
        
        var version_div = $('<div class="version-control">Modification history: </div>')
            .appendTo(buttons)
        $('<select class="version-menu"><option value="">No history</option></select>')
            .appendTo(version_div)
            .attr('disabled', true)
        $('<input type="checkbox" /><label>Commit on Save</label>')
            .appendTo(version_div)
        
		// Save the current values for cancel warning.
		initial_data = _serialize();
		
	}
	
	function _serialize() {
		// Start off with the meta and extraData in place.
		var data = $.extend({}, opts, opts.extraData);
		
		$.each($form.serializeArray(), function(k, v) {
			data[this.name] = this.value;
		});
		return data;
	}
	
	function _commit_click_handler()
	{
	    prompt('Enter commit message:')
	    _save_click_handler()
	}
	
	function _save_click_handler()
	{
		$$.block('Saving. Please wait...');
		
		// Get the data.
		var data = _serialize();
		
		data.method = 'submit_form';
		data.type = opts.type;
		data.id = opts.id ? opts.id : 0;
		
		$.ajax({
		    type: "POST",
		    url: opts.url,
		    data: data,
		    success: _submit_res_handler,
		    dataType: 'json'
		});
	}
	
	function _submit_res_handler(res)
	{
		if (!res.valid) {
			_build_form(res);
		}
		else
		{
			opts.id = res.id;
			$new = $(res.partial).insertAfter($$);
			$$.remove();
			$$ = $new;
			_init();
		}
	}
	
	function _cancel_click_handler()
	{
		// Warn them if there are changes.
		var current_data = _serialize();
		var changed = false;
		for (var key in current_data) {
			if (current_data[key] != initial_data[key]) {
				changed = true;
				break;
			}
		}
		if (changed && !confirm("There are unsaved changes.\n\nAre you sure you want to cancel?"))
		{
			return;
		}
		
		// Clear it out, put the original children back, and re-initialize.
		if (opts.id)
		{
			$$.empty();
			$$.append($children);
			_init();
		}
		else
		{
			$$.remove();
		}
	}
	
	function _delete_click_handler()
	{
		if (!confirm("Are you sure you want to delete this?\n\nIt cannot be recovered."))
		{
			return;
		}
		
		$$.block({
			message: 'Deleting. Please wait...'
		});
		$.ajax({
		    type: "POST",
		    url: opts.url,
		    data: {
		        method: 'delete',
		        id: opts.id
		    },
		    success: function(res) {
    			$$.remove();
    		}
		});
	}
	
	_init();
	
	if (!opts.id) {
		_start_edit();
	}
	
	return this;
};

})(jQuery);