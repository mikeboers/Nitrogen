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
	- preview disabled unless there are changes
	- add flash on invalid form
	- preview should stop moving away from page
	- unsaved changes should stop moving away from page
	
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
			this.edit()
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
		var oldState = this.state
		if (oldState) {
			$$.removeClass('crud-state-' + this.state)
		}
		this.state = state
		$$.addClass('crud')
		$$.addClass('crud-state-' + state)
		assertHoverClass($$)
		
		return oldState
	},
	
	_pulse: function(name, duration, callback) {
		var $$ = this.widget()
		var data = $$.data()
		if (data.crud_pulsing) {
			return false
		}
		data.crud_pulsing = true
		name = 'crud-pulse' + (name ? '-' + name : '')
		$$.addClass(name)
		$$.removeClass(name, duration || 1000, function() {
			data.crud_pulsing = false
		})
		return true
		
	},
	
	_getFormData: function() {
		var data = {}
		$.each(this.form.serializeArray(), function(k, v) {
			data[this.name] = this.value;
		});
		return data;
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
	
	edit: function(e, version)
	{
		var self = this
		var $$ = this.widget()
		
		if (this.state == 'preview') {
			this._restorePreviewForm()
			return
		}
				
		// Block out the UI while we get the form.
		$$.block({
			message: 'Building form...'
		});
		
		
		// Get the form.
		var data = $.extend({}, this.options, this.options.extraData, {
			id: this.options.id ? this.options.id : 0,
			version: version || 0
		});
	
		$.ajax({
			type: "POST",
			url: this.options.url + '/getForm',
			data: data,
			success: this._bound('_setupForm'),
			error: function() {
				$$.unblock({fadeOut: 0})
				alert('There was an error while contacting the server.')
			},
			dataType: 'json'
		});
	},
	
	// This takes an object which must have a `form` property.
	_setupForm: function(res)
	{
		if (this.state != 'idle' && this.state != 'edit') {
			throw 'bad state to setup form'
		}
		
		var $$ = this.widget()
		$$.empty()
		$$.unblock({fadeOut: 0})
		
		// Add an invalid class if this is the response to submitting the form
		// and it being invalid.
		if (res.valid !== undefined && !res.valid) {
			$$.addClass('crud-invalid')
			this._pulse()
		} else {	
			$$.removeClass('crud-invalid')
		}
		
		// Must come after the error classes.
		this._setState('edit')
		
		this.form = $('<form />')
			.appendTo($$)
			.html(res.form) // Must come after the append.
		
		// Save the current values for cancel warning.
		// XXX: do not do this for the edit button on a preview, or after
		// submitting invalid data.
		if (this.originalData === undefined)
			this.originalData = this._getFormData()
		
		if (res.versions !== null) {
			var randomId = 'rand-' + Math.random().toString().slice(2)			
			var versionControls = $('<div class="crud-version-control">History: </div>')
				.appendTo(this.form)
			this.versionSelect = $('<select class="version-menu"></select>')
				.appendTo(versionControls)
			this.commitOnSave = $('<input class="do-commit-version" type="checkbox" />')
				.attr('id', randomId)
				.appendTo(versionControls)
			$('<label class="do-commit-version">Add to history<br/>on save</label>')
				.attr('for', randomId)
				.appendTo(versionControls)
		
			var versions = res.versions || []
			if (versions.length)
			{
				var self = this
			
				$('<option>revert to...</option>')
					.appendTo(this.versionSelect)
				this.versionSelect.change(function(val) {
					var changed = self._isDifferentData(self._getFormData())
					if (changed && !confirm("There are unsaved changes.\n\nAre you sure you want to replace them?"))
						return
					var version = $(this).val()
					self.edit(null, version)				
				})
				$.each(versions, function(i, version) {
					$('<option />')
						.attr('value', version[0])
						.text(version[1])
						.appendTo(self.versionSelect)
				})
			
			}
			else
			{
				this.versionSelect
					.attr('disabled', true)
				$('<option>none</option>')
					.appendTo(this.versionSelect)
			}
		}

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
	
	// Submit the current form data to the server to get either a form back
	// if the data is invalid, or the HTML representation. This has been
	// overloaded to perform the duties of the "save", "preview" and "apply"
	// button.
	//
	// In "save" mode
	save: function(mode)
	{
		if (this.state != 'edit' && this.state != 'preview')
			throw 'cannot save from  ' + this.state
		
		switch(mode) {
			case 'preview':
			case 'apply':
				break
			default:
				mode = 'save'
		}
		
		var self = this
		var $$ = this.widget()
		
		var isPreview = mode == 'preview'
		var isApply = mode == 'apply'
		
		var do_commit_version = !isPreview && this.commitOnSave.attr('checked')
		var version_comment   = !isPreview && do_commit_version ? prompt('Commit comment:') : null
		if (do_commit_version && version_comment === null)
		{
			// They hit cancel.
			return
		}
		
		var blockTarget = isApply ? this.preview : $$
		blockTarget.block({message: isPreview ?
			'Building preview...' :
			'Saving...'
		})
		
		$.ajax({
			type: "POST",
			url: this.options.url + '/' + (isPreview ? 'preview' : 'save'),
			data: $.extend({}, this.options, this._getFormData(), {
				__do_commit_version : do_commit_version ? 'yes' : undefined,
				__version_comment: version_comment || undefined
			}),
			success: this._bound({
					save   : '_handleSaveResponse',
					preview: '_handlePreviewResponse',
					'apply': '_handleApplyResponse'
				}[mode]),
			error: function() {
				blockTarget.unblock({fadeOut: 0})
				alert('There was an error while contacting the server.')
			},
			dataType: 'json'
		})
	},
	
	_handleSaveResponse: function(res)
	{
		if (!res.valid) {
			this._setupForm(res);
		}
		else
		{
			// Anything the server passes down (ie. new ID) will get merged
			// into the existing options when passed along to the new CRUD
			// setup.
			var options = $.extend(this.options, res)
			
			var $$ = this.widget()
			$(res.html)
				.insertAfter($$)
				.crud(options)
			$$.remove()
		}
	},
	
	preview: function() {
		this.save('preview')
	},
	
	_handlePreviewResponse: function(res)
	{
		if (!res.valid) {
			this._setupForm(res);
		}
		else
		{			
			$$ = this.widget()
			$$.unblock({fadeOut: 0})
			this.preview = $(res.html)
				.insertAfter($$)
			$$.hide()	
			
			this._setState('preview')
			this._setState('preview', this.preview)
			
			var $buttons = $('<div class="crud-buttons" />')
				.appendTo(this.preview)
			$('<a>Save</a>')
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
	
	_restorePreviewForm: function() {
		var $$ = this.widget()
		this.preview.remove()
		$$.removeClass('crud-invalid')
		$$.show()
		this._setState('edit')
	},

	apply: function() {
		if (this.state != 'preview')
			throw 'not previewing'
		this.save('apply')
		
	},
	
	_handleApplyResponse: function(res) {
		this.preview.remove()
		this._handleSaveResponse(res)
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
	// This also needs to be quoted for those browsers that care that much.
	'delete': function()
	{
		var $$ = this.widget()
		
		if (!confirm("Are you sure you want to delete this?\n\nIt cannot be recovered."))
			return
		
		$$.block({
			message: 'Deleting...'
		});
		
		$.ajax({
			type: "POST",
			url: this.options.url + '/delete',
			data: {
				id: this.options.id
			},
			success: function(res) {
				$$.remove();
			},
			error: function() {
				$$.unblock({fadeOut: 0})
				alert('There was an error while contacting the server.')
			},
		});
	}

});

})(jQuery);