/*

Text area selection manipulation plugin.
By Mike Boers.
mail@mikeboers.com

I actually didn't write the core of these, and honestly cant remember where I
did get them from. Sorry.

*/

(function($)
{

	// get the selection
	$.fn.getSelection = function() {
		
		var $$ = this;
		var textarea = this[0];
		
		$$.focus();
		
		
		var ret = {}
		ret.start = -1;
		
		if (document.selection)
		{
			ret.text = document.selection.createRange().text;
			if ($.browser.msie)
			{
				var range = document.selection.createRange()
				var rangeCopy = range.duplicate();
				rangeCopy.moveToElementText($$);
				while(rangeCopy.inRange(range)) { // fix most of the ie bugs with linefeeds...
					rangeCopy.moveStart('character');
					ret.start++;
				}
			} else { // opera
				ret.start = textarea.selectionStart;
			}
		} else { // gecko
			ret.start = textarea.selectionStart;
			ret.text = $$.val().substring(ret.start, textarea.selectionEnd);
		}
		
		ret.length = ret.text.length;
		ret.end = ret.start + ret.length;
		return ret;
	}

	// Set the selection range.
	// If you want to insert the cursor somewhere, pass len=0
	$.fn.setSelection = function(start, len)
	{
		var $$ = this;
		var textarea = this[0];
		
		// To restore later.
		var scroll_pos = textarea.scrollTop;
		
		if (textarea.createTextRange){
			// quick fix to make it work on Opera 9.5
			if ($.browser.opera && $.browser.version >= 9.5 && len == 0) {
				return false;
			}
			range = textarea.createTextRange();
			range.collapse(true);
			range.moveStart('character', start); 
			range.moveEnd('character', len); 
			range.select();
		} else if (textarea.setSelectionRange ){
			textarea.setSelectionRange(start, start + len);
		}
		
		textarea.scrollTop = scroll_pos;
		textarea.focus();
		
		return this;
	}
	
	// Replace the current selection with something.
	// Pass a string to insert it.
	// Pass a function that returns new text from the old text.
	$.fn.replaceSelection = function(input)
	{
		var $$ = this;
		var textarea = this[0];
		var selection = this.getSelection();
		
		if (input.call)
		{
			input = input(selection.text);
		}
		
		$$.focus();
		
		if (document.selection) {
			var newSelection = document.selection.createRange();
			newSelection.text = input;
		} else {
			var prev = $$.val();
			$$.val(
				prev.substring(0, selection.start) +
				input +
				prev.substring(selection.start + selection.length, prev.length)
			);
		}
		
		$$.setSelection(selection.start + input.length, 0);
		
		return this;
	}
	

})(jQuery);