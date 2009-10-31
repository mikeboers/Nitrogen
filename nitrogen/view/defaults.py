
defaults = {}
defaults['nl2br'] = lambda s: s.replace("\n", "<br />")
defaults['json'] = json.dumps
defaults['markdown'] = lambda x: clean_html(markdown(x.encode('utf8'))).decode('utf8')
defaults['format_date'] = lambda d, f: (d.strftime(f) if d else '')
defaults['randomize'] = lambda x: sorted(x, key=lambda y: random.random())
defaults['sorted'] = sorted
defaults['repr'] = repr
defaults['textblob'] = textblob
defaults['textblob_md'] = markdownblob
defaults['truncate'] = webhelpers.text.truncate
defaults['html'] = HTML
defaults['urlify_name'] = urlify_name