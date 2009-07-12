<div class="textblob">
	## Unfortunately this does need to have a div wrapper around the p. I
	## wanted to just have a p with the content, but the way the editable works
	## it wont really allow it. We could go and show different markup for admin
	## vs not, but I'm lazy.
	% if is_admin_area:
	<!--{id:${blob.id}}-->
	% endif
	<p>${blob.value|h}</p>
</div>