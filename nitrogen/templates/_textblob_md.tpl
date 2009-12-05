% if is_admin_area:
<script type="text/javascript">jQuery(function($){
	$("#textblob_md-${blob.key|h}").editable({
		id: ${blob.id|json},
		url: '/_textblob_md',
		deleteable: false
	});
})</script>
% endif
<div id="textblob_md-${blob.key|h}" class="textblob_md">
	${markdown(blob.value)}
</div>