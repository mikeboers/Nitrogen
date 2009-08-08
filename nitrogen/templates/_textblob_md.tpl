<div id="textblob_md-${blob.key|h}" class="textblob_md">
	% if is_admin_area and (permission is None or (user and user.has_permission(permission))):
	<!--{id:${blob.id}}-->
	% endif
	${markdown(blob.value)}
</div>