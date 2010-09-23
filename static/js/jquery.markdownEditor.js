(function($){
	
	$.markdownEditor = {
		defaults: {
			help_link: "http://daringfireball.net/projects/markdown/",
			commands: [
				{
					name: 'Bold',
					key: 'B',
					replace: function(input)
					{
					    return '**' + input + '**';
					}
				},
				{
					name: 'Italic',
					key: 'I',
					replace: function(input)
					{
					    return '*' + input + '*';
					}
				},
				{
				    name: "Link",
				    key: 'L',
				    replace: function(input)
				    {
				        // Get the url from them.
				        var url = prompt("Enter a URL");
				        if (url) {
							return '[' + (input ? input : 'Link text here') + '](' + url + ')';
						}
						return input
				    }
				},
				{
				    name: "List Item",
				    replace: function(input)
				    {
				        return '- ' + input;
				    }
				},
				{
				    name: "Image",
				    replace: function(input)
				    {
			        	var url = prompt("Enter an image URL");
			        	if (url) {
							return '![' + (input ? input : 'Link text here') + '](' + url + ')';
						}
						return input
				    }
				},
				{
				    name: "Horizontal Rule",
				    replace: function(input)
				    {
				        return '\n***\n';
				    }
				}
			]
		}
	};
	
	$.fn.markdownEditor = function(opts)
	{
		if (!opts) {
			opts = $.markdownEditor.defaults;
		}
		
		var $$ = this;
		$$.addClass('markdown-editor-area');
		$$.wrap('<div class="markdown-editor" />');
		var buttons = $('<div class="buttons" />')
		    .insertBefore($$);
		$$.wrap('<div class="wrapper" />');
		
        /*
        $$.resizable({
                    minHeight: opts.minHeight ? opts.minHeight : 100,
                    handles: 's'
                });
        
        //*/
        $$.parent().TextAreaResizer();
        
		// Build the button list.
		for (var i in opts.commands)
		{
			(function(cmd){
				$('<a href="#">&nbsp</a>')
					.addClass('button-' + cmd.name.toLowerCase().replace(/\W+/, '_'))
					.attr('title', cmd.name + (cmd.key ? ': Ctrl-' + cmd.key.toUpperCase() : ''))
					.appendTo(buttons)
					.click(function(e)
					{
						e.preventDefault();
						if (cmd.trigger)
						{
						    cmd.trigger($$);
						}
						else if (cmd.replace)
						{
						    $$.replaceSelection(cmd.replace);
						}
					});
			})(opts.commands[i]);
		}
		
		if (opts.help_link)
		{
			$('<a class="button-help" target="_blank">&nbsp;</a>').attr('href', opts.help_link).appendTo(buttons);
		}
	
		// Handle key presses
		$$.keydown(function(e)
		{
			if (e.ctrlKey || e.metaKey)
			{
				for (var i in opts.commands)
				{
					var cmd = opts.commands[i];
					if (cmd.key && cmd.key.toLowerCase() == String.fromCharCode(e.keyCode).toLowerCase())
					{
        				e.preventDefault()
        				e.stopPropagation()
						$$.replaceSelection(cmd.replace);
					}
				}
			}
		});	
	
		return this;	
	}

})(jQuery);