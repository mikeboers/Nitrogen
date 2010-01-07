% if is_admin_area and (permission is None or user.has_permission(permission)):
<script type="text/javascript">jQuery(function($){
	$("#textblob-${blob.key|h}").editable({
		id: ${blob.id|json},
		url: '/_textblob',
		deleteable: false
	});
})</script>
% endif
<div id="textblob-${blob.key|h}" class="textblob">
	## Unfortunately this does need to have a div wrapper around the p. I
	## wanted to just have a p with the content, but the way the editable works
	## it wont really allow it. We could go and show different markup for admin
	## vs not, but I'm lazy.
	<p>${blob.value|h}</p>
</div>