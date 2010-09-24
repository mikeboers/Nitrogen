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
	
	- √ edit
	- √ delete
	- √ save
	- √ cancel
	- √ preview
	- preview apply
	- preview edit
	- preview revert
	
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
		
		// This is what we will restore to.
		this.originalChildren = $$.children()
		
		
		if (this.options.id) {
			this._setupIdle()
		} else if (this.options.allowCreate) {
			console.warning('Creation has not been fixed yet.')
			// this.edit()
		} else {
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
	
	_setState: function(state, obj) {
		var $$ = obj ? obj : this.widget()
		var oldDate = this.state
		if (oldDate) {
			$$.removeClass('crud-state-' + this.state)
		}
		this.state = state
		$$.addClass('crud')
		$$.addClass('crud-state-' + state)
		assertHoverClass($$)
		return oldDate
	},
	
	_getFormData: function() {
		var data = {}
		$.each(this.form.serializeArray(), function(k, v) {
			data[this.name] = this.value;
		});
		return data;
	},
	
	_getRequestData: function() {
		return $.extend({}, this.options, this.options.extraData, this._getFormData())
	},
	
	_setupIdle: function() {
				
		this._setState('idle')
		
		var $$ = this.widget();
		
		
		this.buttons = $('<div class="crud-buttons" />')
			.appendTo($$)
		
		if (this.options.allowUpdate) {
			$('<a class="edit-button">Edit</a>')
				.button({icons: {primary: 'silk-icon silk-icon-pencil'}})
				.click(this._bound('edit'))
				.appendTo(this.buttons)
		}

		if (this.options.allowDelete) {
			$('<a class="delete-button">Delete</a>')
				.button({icons: {primary: 'silk-icon silk-icon-delete'}})
				.click(this._bound('delete'))
				.appendTo(this.buttons)
		}
		
		this.buttons.buttonset()
		
	},
	
	edit: function()
	{
		var self = this
		var $$ = this.widget()
		
		var oldState = this._setState('getForm')
		
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
			success: this._bound('_setupForm'),
			error: function() {
				self._setState(oldState)
				$$.unblock()
				alert('There was an error while contacting the server.')
			},
			dataType: 'json'
		});
	},
	
	// This takes an object which must have a `form` property.
	_setupForm: function(res)
	{
		var $$ = this.widget()
		$$.unblock()
		$$.empty()
		
		this._setState('edit')
	
		this.form = $('<form />')
			.appendTo($$)
			.html(res.form) // Must come after the append.
		
		// Save the current values for cancel warning.
		// XXX: do not do this for the edit button on a preview, or after
		// submitting invalid data.
		if (this.originalData === undefined)
			this.originalData = this._getFormData()
		
		var versionControls = $('<div class="version-control">History: </div>')
			.appendTo(this.form)
		$('<select class="version-menu"><option value="">None</option></select>')
			.attr('disabled', true)
			.appendTo(versionControls)
		$('<input type="checkbox" /><label>Commit on Save</label>')
			.appendTo(versionControls)
		
		var buttons = $('<div class="crud-buttons" />')
			.appendTo(this.form);
		$('<a class="preview-button">Preview</a>')
			.button({icons: {primary: 'silk-icon silk-icon-eye'}})
			.click(this._bound('preview'))
			.appendTo(buttons)
		$('<a class="save-button">Save</a>')	
			.button({icons: {primary: 'silk-icon silk-icon-tick'}})
			.click(this._bound('save'))
			.appendTo(buttons)
		$('<a class="cancel-button">Cancel</a>')	
			.button({icons: {primary: 'silk-icon silk-icon-cross'}})
			.click(this._bound('cancel'))
			.appendTo(buttons)
		buttons.buttonset()
	},
	
	cancel: function()
	{
		if (this.state != 'edit')
			throw 'not editing'
		
		var changed = this._isDifferentData(this._getFormData())
		if (changed && !confirm("There are unsaved changes.\n\nAre you sure you want to cancel?"))
			return
		
		var $$ = this.widget()
		
		if (this.options.id) { // an UPDATE
			// Restore the markup to what it was.
			$$.empty()
			$$.append(this.originalChildren)
			this._setupIdle()
		} else { // a CREATE
			$$.remove()
		}
	},
	
	save: function(preview)
	{
		if (this.state != 'edit')
			throw 'not editing'
		
		var self = this
		var oldState = this._setState(preview ? 'preview' : 'saving')
		var $$ = this.widget()
		
		$$.block(preview ?
			'Building preview. Please wait...' :
			'Saving. Please wait...'
		)
	
		$.ajax({
			type: "POST",
			url: this.options.url,
			data: $.extend(this._getRequestData(), {
				method: preview ? 'preview' : 'submit_form',
				id: this.options.id ? this.options.id : 0
			}),
			success: this._bound(preview ? '_handlePreviewResponse' : '_handleSaveResponse'),
			error: function() {
				self._setState(oldState)
				$$.unblock()
				alert('There was an error while contacting the server.')
			},
			dataType: 'json'
		})
	},
	
	preview: function() {
		this.save(true)
	},
	
	_handleSaveResponse: function(res)
	{
		if (!res.valid) {
			this._setupForm(res);
		}
		else
		{
			if (res.id)
				// So the next will be an update.
				this.options.id = res.id
			var $$ = this.widget()
			$(res.partial)
				.insertAfter($$)
				.crud(this.options)
			$$.remove()
		}
	},
	
	_handlePreviewResponse: function(res)
	{
		if (!res.valid) {
			this._setupForm(res);
		}
		else
		{			
			$$ = this.widget()
			this.preview = $(res.partial)
				.insertAfter($$)
			$$.hide()
			
			this._setState('preview')
			this._setState('preview', this.preview)
			
			var $buttons = $('<div class="crud-buttons" />')
				.appendTo(this.preview)
			$('<a>Apply</a>')
					.button({icons: {primary: 'silk-icon silk-icon-tick'}})
					.click(this._bound('apply'))
					.appendTo($buttons);
			$('<a>Edit</a>')
				.button({icons: {primary: 'silk-icon silk-icon-pencil'}})
				.click(this._bound('edit'))
				.appendTo($buttons);
			$('<a>Revert</a>')
				.button({icons: {primary: 'silk-icon silk-icon-cross'}})
				.click(this._bound('revert'))
				.appendTo($buttons);
			$buttons.buttonset();
		}
	},

	_isDifferentData: function(data)
	{
		for (var key in data) {
			if (data[key] != this.originalData[key]) {
				return true
			}
		}
		return false
	},
	
	
	revert: function() {
		
		if (this.state != 'preview')
			throw 'not editing'
		
		var changed = this._isDifferentData(this._getFormData())
		if (changed && !confirm("There are unsaved changes.\n\nAre you sure you want revert changes?"))
			return
		
		this.preview.remove()
		
		var $$ = this.widget()
		
		if (this.options.id) { // an UPDATE
			// Restore the markup to what it was.
			$$.empty()
			$$.append(this.originalChildren)
			$$.show()
			this._setupIdle()
		} else { // a CREATE
			$$.remove()
		}
		
	},

	// Note that this is NOT "destroy". This actually removes the data.
	delete: function()
	{
		var $$ = this.widget()
		
		if (!confirm("Are you sure you want to delete this?\n\nIt cannot be recovered."))
			return
		
		this._setState('deleting')
		
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