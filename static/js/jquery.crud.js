/*

This is the editable plugin for Mike Boers' nitrogen web framework.

Requirments:

	jquery-ui
	jquery.blockUI.js
	
Optional:
	jquery.autodate.js
	jquery.markdownEditor.js
	jquery.textarearesizer.js

*/

(function($, undefined) {

var bind = function(context, func)
{
	return function()
	{
		return func.apply(context, arguments)
	}
}

$.widget('nitrogen.crud', {
	
	options: {
		deleteable: true,

		// Extra data to send along with the API request.
		// Useful for when you need more info for an API mdoel adapter callback.
		extraData: {}
	},
	
	_init: function()
	{
		
		var self = this
		var $$ = this.element
		
		$$.hover(function(){
			$$.addClass('crud-hover')
		}, function(){
			$$.removeClass('crud-hover')
		})
		
		$$.addClass('crud');
		$$.removeClass('crud-active');
	
		this.children = $$.children();
		this.outerButtons = $('<div class="outer-buttons" />')
			.appendTo($$);
	
		// Add the edit button.
		$('<a class="edit-button">Edit</a>')
			.button({icons: {primary: 'silk-icon silk-icon-pencil'}})
			.click(bind(this, this._start_edit))
			.appendTo(this.outerButtons);
	
		if (this.options.deleteable)
		{
			$('<a class="delete-button">Delete</a>')
				.button({icons: {primary: 'silk-icon silk-icon-delete'}})
				.click(bind(this, this._delete_click_handler))
				.appendTo(this.outerButtons);
		}
	
		this.outerButtons.buttonset();
		
		if (!this.options.id) {
			this._start_edit()
		}
	},

	_start_edit: function()
	{
		var $$ = this.element;
		
		// Block out the UI while we get the form.
		$$.block({
			message: 'Retrieving form. Please wait...'
		});
	
		// Get the form.
		var data = $.extend({}, this.options, this.options.extraData, {
			method: 'get_form',
			id: this.options.id ? this.options.id : 0
		});
	
		$.ajax({
			type: "POST",
			url: this.options.url,
			data: data,
			success: bind(this, this._build_form),
			error: function() {
				$$.unblock();
				alert('There was an error while contacting the server.');
			},
			dataType: 'json'
		});
	},
	
	_build_form: function(res)
	{
		var $$ = this.element;
		// Unblock the UI, strip all the children, place the form.
		$$.unblock();
		$$.empty();
		$$.addClass('crud-active');
	
		var $wrapper = $('<div class="wrapper" />').appendTo($$);
		this.form = $('<form />').appendTo($wrapper);
		this.form.html(res.form);
	
		var buttons = $('<div class="inner-buttons" />')
			.appendTo(this.form);
	
		// Add the buttons.
	
		$('<a class="commit-button">Preview</a>')
			.button({icons: {primary: 'silk-icon silk-icon-eye'}, disabled:true})
			.appendTo(buttons)
			// .click(_commit_click_handler);
	
		$('<a class="save-button">Save</a>')	
			.button({icons: {primary: 'silk-icon silk-icon-tick'}})
			.appendTo(buttons)
			.click(bind(this, this._save_click_handler));
		$('<a class="cancel-button">Cancel</a>')	
			.button({icons: {primary: 'silk-icon silk-icon-cross'}})
			.appendTo(buttons)
			.click(bind(this, this._cancel_click_handler));
	
		var version_div = $('<div class="version-control">History: </div>')
			.appendTo(buttons)
		$('<select class="version-menu"><option value="">None</option></select>')
			.appendTo(version_div)
			.attr('disabled', true)
		$('<input type="checkbox" /><label>Commit on Save</label>')
			.appendTo(version_div)
	
		// Save the current values for cancel warning.
		this.initialData = this._serialize();
	
	},
	
	_serialize: function() {
		// Start off with the meta and extraData in place.
		var data = $.extend({}, this.options, this.options.extraData);
	
		$.each(this.form.serializeArray(), function(k, v) {
			data[this.name] = this.value;
		});
		return data;
	},
	
	_commit_click_handler: function()
	{
		prompt('Enter commit message:')
		_save_click_handler()
	},

	_save_click_handler: function()
	{
		var $$ = this.element
		$$.block('Saving. Please wait...');
	
		// Get the data.
		var data = this._serialize();
	
		data.method = 'submit_form';
		data.type = this.options.type;
		data.id = this.options.id ? this.options.id : 0;
	
		$.ajax({
			type: "POST",
			url: this.options.url,
			data: data,
			success: bind(this, this._submit_res_handler),
			dataType: 'json'
		});
	},

	_submit_res_handler: function(res)
	{
		var $$ = this.element;
		if (!res.valid) {
			this._build_form(res);
		}
		else
		{
			this.options.id = res.id;
			$new = $(res.partial).insertAfter($$);
			$$.remove();
			this.element = $new;
			this._init();
		}
	},

	_cancel_click_handler: function()
	{
		var $$ = this.element
		// Warn them if there are changes.
		var current_data = this._serialize();
		var changed = false;
		for (var key in current_data) {
			if (current_data[key] != this.initialData[key]) {
				changed = true;
				break;
			}
		}
		if (changed && !confirm("There are unsaved changes.\n\nAre you sure you want to cancel?"))
		{
			return;
		}
	
		// Clear it out, put the original children back, and re-initialize.
		if (this.options.id)
		{
			$$.empty();
			$$.append(this.children);
			this._init();
		}
		else
		{
			$$.remove();
		}
	},

	_delete_click_handler: function()
	{
		var $$ = this.element
		
		if (!confirm("Are you sure you want to delete this?\n\nIt cannot be recovered."))
		{
			return;
		}
	
		$$.block({
			message: 'Deleting. Please wait...'
		});
		$.ajax({
			type: "POST",
			url: this.options.url,
			data: {
				method: 'delete',
				id: this.options.id
			},
			success: function(res) {
				$$.remove();
			}
		});
	}

});

})(jQuery);