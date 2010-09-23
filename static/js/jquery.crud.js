/*

This is the editable plugin for Mike Boers' nitrogen web framework.

Requirments:

	jquery-ui
	jquery.blockUI.js
	
Optional:
	jquery.autodate.js
	jquery.markdownEditor.js
	jquery.textarearesizer.js

TODO:
	- make sure only serialized data is being tracked for changes
	
*/

(function($, undefined) {


var assertHoverClass = function($$) {
	if (!$$.data().crudHoverSetup) {
		$$.hover(function() {
			$$.addClass('crud-hover')
		}, function() {
			$$.removeClass('crud-hover')
		})
		$$.data().crudHoverSetup = true
	}
}


$.widget('nitrogen.crud', {
	
	options: {
		
		allowCreate: true,
		allowUpdate: true,
		allowDelete: true,
		
		// Extra data to send along with the API request.
		// Useful for when you need more info for an API mdoel adapter callback.
		extraData: {}
	},	
	
	_create: function()
	{
		// For backwards compatibility
		if (this.options.deleteable !== undefined) {
			this.options.allowDelete = this.options.deleteable
		}
		
		var $$ = this.widget()
		
		$$.addClass('crud')
		assertHoverClass($$)
		
		if (this.options.id) {
			this._setupIdle()
		} else if (this.options.allowCreate) {
			console.warning('Creation has not been fixed yet.')
			// this._request_form()
		} else {
			this.widget().removeClass('crud')
			throw "no ID and no create permissions"
		}
	},
	
	// Get functions whose context is bound to this object.
	_bound: function(name) {
		if (!this._boundFunctions) {
			this._boundFunctions = {}
		}
		if (!this._boundFunctions[name]) {
			var self = this
			var func = this[name]
			this._boundFunctions[name] = function() {
				return func.apply(self, arguments)
			}
		}
		return this._boundFunctions[name]
	},
	
	_setState: function(state) {
		var $$ = this.widget()
		if (this.state) {
			$$.removeClass('crud-state-' + this.state);
		}
		this.state = state;
		$$.addClass('crud-state-' + state);
	},
	
	_setupIdle: function() {
				
		this._setState('idle')
		
		var $$ = this.widget();
		
		this.buttons = $('<div class="crud-buttons" />')
			.appendTo($$)
		
		if (this.options.allowUpdate) {
			$('<a class="edit-button">Edit</a>')
				.button({icons: {primary: 'silk-icon silk-icon-pencil'}})
				.click(this._bound('_request_form'))
				.appendTo(this.buttons)
		}

		if (this.options.allowDelete) {
			$('<a class="delete-button">Delete</a>')
				.button({icons: {primary: 'silk-icon silk-icon-delete'}})
				.click(this._bound('_delete_click_handler'))
				.appendTo(this.buttons)
		}
		
		this.buttons.buttonset()
		
	},
	
	// 
	// 	
	// 	if (!preview)
	// 	{
	// 		this.children = $$.children();
	// 	}
	// 	
	// 	var $buttons = 
	// 		.appendTo($$);
	// 	this.outerButtons = $buttons
	// 	
	// 	if (preview)
	// 	{
	// 		this.element.addClass('crud-preview')
	// 		
	// 		// Add the edit button.
	// 		$('<a>Apply</a>')
	// 			.button({icons: {primary: 'silk-icon silk-icon-tick'}})
	// 			.click(this._bound('_apply_preview'))
	// 			.appendTo($buttons);
	// 			
	// 		// Add the edit button.
	// 		$('<a>Edit</a>')
	// 			.button({icons: {primary: 'silk-icon silk-icon-pencil'}})
	// 			.click(this._bound('_edit_preview'))
	// 			.appendTo($buttons);
	// 			
	// 		// Add the edit button.
	// 		$('<a>Revert</a>')
	// 			.button({icons: {primary: 'silk-icon silk-icon-cross'}})
	// 			.click(this._bound('_revert_preview'))
	// 			.appendTo($buttons);
	// 			
	// 	}
	// 	else
	// 	{
	// 		
	// 	}
	// 	
	// 	$buttons.buttonset();
	// },

	
	_init_preview: function()
	{
		this._init(true)
	},
	
	_request_form: function()
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
			success: this._bound('_insert_form'),
			error: function() {
				$$.unblock();
				alert('There was an error while contacting the server.');
			},
			dataType: 'json'
		});
	},
	
	_insert_form: function(res)
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
	
		$('<a class="preview-button">Preview</a>')
			.button({icons: {primary: 'silk-icon silk-icon-eye'}, disabled:false})
			.appendTo(buttons)
			.click(this._bound('_preview_click_handler'));
	
		$('<a class="save-button">Save</a>')	
			.button({icons: {primary: 'silk-icon silk-icon-tick'}})
			.appendTo(buttons)
			.click(this._bound('_save_click_handler'));
		
		$('<a class="cancel-button">Cancel</a>')	
			.button({icons: {primary: 'silk-icon silk-icon-cross'}})
			.appendTo(buttons)
			.click(this._bound('_cancel_click_handler'));
	
		buttons.buttonset()
			
		var version_div = $('<div class="version-control">History: </div>')
			.appendTo(buttons)
		$('<select class="version-menu"><option value="">None</option></select>')
			.appendTo(version_div)
			.attr('disabled', true)
		$('<input type="checkbox" /><label>Commit on Save</label>')
			.appendTo(version_div)
		
		
		// Save the current values for cancel warning.
		this.initialData = this._getData();
	
	},
	
	_getData: function() {
		// Start off with the meta and extraData in place.
		var data = $.extend({}, this.options, this.options.extraData);
		$.each(this.form.serializeArray(), function(k, v) {
			data[this.name] = this.value;
		});
		return data;
	},

	_save_click_handler: function()
	{
		var $$ = this.element
		$$.block('Saving. Please wait...');
	
		// Get the data.
		var data = this._getData();
	
		data.method = 'submit_form';
		data.id = this.options.id ? this.options.id : 0;
	
		$.ajax({
			type: "POST",
			url: this.options.url,
			data: data,
			success: this._bound('_submit_res_handler'),
			dataType: 'json'
		});
	},

	_submit_res_handler: function(res)
	{
		var $$ = this.element;
		if (!res.valid) {
			this._insert_form(res);
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
	
	_preview_click_handler: function()
	{
		var $$ = this.element
		$$.block('Saving. Please wait...');
	
		// Get the data.
		var data = this._getData();
		
		data.method = 'preview';
		data.id = this.options.id ? this.options.id : 0;
		
		this.previewData = data;
		
		$.ajax({
			type: "POST",
			url: this.options.url,
			data: data,
			success: this._bound('_preview_res_handler'),
			dataType: 'json'
		});
	},

	_preview_res_handler: function(res)
	{
		var $$ = this.element;
		if (!res.valid) {
			this._insert_form(res);
		}
		else
		{
			this.previewForm = this.element
			this.previewForm.hide()
			this.element = $(res.partial).insertAfter(this.element);
			this._init_preview();
		}
	},

	_isDifferentData: function(data)
	{
		for (var key in data) {
			if (data[key] != this.initialData[key]) {
				return true
			}
		}
		return false
	},
	
	_cancel_click_handler: function()
	{
		var changed = this._isDifferentData(this._getData())
		if (changed && !confirm("There are unsaved changes.\n\nAre you sure you want to cancel?"))
		{
			return;
		}
		
		var $$ = this.element
		
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
	
	_revert_preview: function()
	{
		console.log(this)
		var changed = this._isDifferentData(this.previewData)
		if (changed && !confirm("There are unsaved changes.\n\nAre you sure you want to revert changes?"))
		{
			return;
		}
		
		var $$ = this.element
		
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