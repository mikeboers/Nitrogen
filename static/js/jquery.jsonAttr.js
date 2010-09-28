/*
 * Metadata - jQuery plugin for parsing metadata from elements
 *
 * Copyright (c) 2006 John Resig, Yehuda Katz, J�örn Zaefferer, Paul McLanahan
 *
 * Dual licensed under the MIT and GPL licenses:
 *   http://www.opensource.org/licenses/mit-license.php
 *   http://www.gnu.org/licenses/gpl.html
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
    - Default name is comments.
    - Removed class name.
    - Removed elem name.
    - Removed defaults and settings ENTIRELY. Supply a false value or
      "__comment__" for the comment data, and any string for attribute data.
    - Attribute parsing is more strict (must be an object).
    - I have discovered that it must return an empty object for the validation
      plugin to work properly. (And I don't want to modify that plugin too.)
    - Added $.metadata.exists to deal with lack of null because of the point
      above. (*le sigh*)
*/


(function($) {

$.jsonAttr = {
    getRaw: function(elem, name)
    {
        name = name || 'data';
        var cacheKey = 'jsonAttr-' + name;
        var data = $.data(elem, cacheKey);
        if (data !== undefined)
        {
            return data;
        }
        var data = $.parseJSON($(elem).attr(name));
        $.data(elem, cacheKey, data);
        return data;
    },
    get: function(elem, name)
    {
        var res = $.jsonAttr.getRaw(elem, name);
        return res ? res : {};
    }
};

$.fn.jsonAttr = function(name)
{
    return $.jsonAttr.get(this[0], name);
};

})(jQuery);