
def textblob(key, permission=None):
    blob = session.query(TextBlob).filter_by(key=key).first()
    if not blob:
        blob = TextBlob(key=key, value='JUST CREATED. Add some content!')
        session.add(blob)
        session.commit()
    return render('_textblob.tpl', blob=blob, permission=permission)

def markdownblob(key, permission=None):
    blob = session.query(MarkdownBlob).filter_by(key=key).first()
    if not blob:
        blob = MarkdownBlob(key=key, value='**JUST CREATED.** *Add some content!*')
        session.add(blob)
        session.commit()
    return render('_textblob_md.tpl', blob=blob, permission=permission)