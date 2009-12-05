<div id="textblob_md-${blob.key|h}" class="textblob_md">
	% if is_admin_area:
	<!--{id:${blob.id}}-->
	% endif
	${markdown(blob.value)}
</div>