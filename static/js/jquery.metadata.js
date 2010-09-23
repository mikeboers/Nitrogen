/*
 * Metadata - jQuery plugin for parsing metadata from elements
 *
 * Copyright (c) 2006 John Resig, Yehuda Katz, J�örn Zaefferer, Paul McLanahan
 *
 * Dual licensed under the MIT and GPL licenses:
 *	 http://www.opensource.org/licenses/mit-license.php
 *	 http://www.gnu.org/licenses/gpl.html
 *
 * Revision: $Id: jquery.metadata.js 3640 2007-10-11 18:34:38Z pmclanahan $
 *
 */

/*
 * commentData
 * Author: James Padolsey
 */

/*

Mike Boers.
mail@mikeboers.com

This is a jQuery plugin that parses metadata objects (JSON formatted) from HTML
comments or attributes.

To retrieve the data from the first child comment (that appears to be JSON) of
a given node:

	data = $elem.metadata();
		-- OR --
	data = $elem.metadata(null);
			-- OR --
	data = $elem.metadata('__comment__');

To retrieve the data from an attribute on a node:

	data = $elem.metadata('attribute_name');

When searching for comment data, it attempts to parse the first one which has
the slightest resemblance to a JSON object. It that fails, it does NOT keep
looking in more comments.

The data is cached the first time it is queried for (and the cache is
seperate for comments and different attributes). It will continue to return
the same data if you modify the attribute or comment contents. Therefor, this
is designed as a data transfer mechanism from the server to the client, ONLY.

This has been scraped together from the Metadata plugin and the commentData
script, which can be found at:
	http://plugins.jquery.com/project/metadata
	http://james.padolsey.com/javascript/metadata-within-html-comments/

Changes:
	- Default type is comments.
	- Removed class type.
	- Removed elem type.
	- Removed defaults and settings ENTIRELY. Supply a false value or
	  "__comment__" for the comment data, and any string for attribute data.
	- Attribute parsing is more strict (must be an object).
	- I have discovered that it must return an empty object for the validation
	  plugin to work properly. (And I don't want to modify that plugin too.)
	- Added $.metadata.exists to deal with lack of null because of the point
	  above. (*le sigh*)
*/


(function($) {
	

// Return a list of all comments within the DOM element given.
var getAllComments = function(elem)
{
	var comments = [];
	var node = elem.firstChild;
	if (!node)
	{
		return comments;
	}
	do
	{
		if (node.nodeType === 8)
		{
			comments[comments.length] = node;
		}
		if (node.nodeType === 1)
		{
			comments = comments.concat(getAllComments(node));
		}
	} while (node = node.nextSibling);
	return comments;
};

json_pattern = /^\s*?\{.+\}\s*?$/;


$.metadata = {
	exists: function(elem, type)
	{
		$.metadata.getRaw(elem, type) !== null;
	},
	getRaw: function(elem, type)
	{
		if (!type) {
			type = '__comment__';
		}
		var dataKey = 'metadata-' + type;
	
		// Return cached data if it already exists.
		var data = $.data(elem, dataKey);
		if (data != undefined)
		{
			return data;
		}
	
		data = null;
	
		// Pull the data from the first comment that looks like data.
		if (type == '__comment__')
		{	
			var comments = getAllComments(elem);
			var comment;
			var i = 0;
			
			// Changed to look for FIRST comment.
			while (i < comments.length) {
				comment = comments[i].data;
				// Pull out unnessesary whitespace. We error if we leave
				// it in. 
				comment = comment.replace(/\n|\r\n/g, '');
				if (json_pattern.test(comment)) {
					data = comment;
					break;
				}
				i++;
			}
		}
	
		// Pull the attribute data out.
		else if (elem.getAttribute != undefined)
		{
			var attr = elem.getAttribute(type);
			if (attr && json_pattern.test(attr))
			{
				data = attr;
			}
		}
	
		if (data)
		{
			if (data.indexOf('{') < 0)
			{
				data = "{" + data + "}";
			}
			data = eval("(" + data + ")");
		}
		
		$.data(elem, dataKey, data);
		
		return data;
	},
	get: function(elem, type)
	{
	    var data = $.metadata.getRaw(elem, type);
	    return data ? data : {};
	}
};

/**
 * Returns the metadata object for the first member of the jQuery object.
 */
$.fn.metadata = function(type)
{
	return $.metadata.get(this[0], type);
};

$.fn.metadataExists = function(type){
	return $.metadata.exists(this[0], type);
}

})(jQuery);