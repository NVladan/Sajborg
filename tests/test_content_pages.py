"""Tech Magazin, O nama, pravne stranice."""

from extensions import db
from models import Post, User


def make_post(slug, title, published=True, words=400):
    author = User.query.first()
    if author is None:
        author = User(username='autor', email='autor@example.com', role='admin')
        author.set_password('Autor123!')
        db.session.add(author)
        db.session.flush()
    post = Post(title=title, slug=slug, content='<p>' + ' '.join(['riječ'] * words) + '</p>',
                author_id=author.id, is_published=published)
    db.session.add(post)
    db.session.commit()
    return post


def test_blog_list_shows_lead_and_reading_time(client):
    make_post('prvi', 'Prvi članak')
    make_post('drugi', 'Drugi članak')
    make_post('skriven', 'Nacrt članka', published=False)
    html = client.get('/tech-magazin/').get_data(as_text=True)
    assert 'Prvi članak' in html and 'Drugi članak' in html
    assert 'Nacrt članka' not in html
    assert '2 min čitanja' in html


def test_post_detail_has_more_and_cta(client):
    make_post('a', 'Članak A')
    make_post('b', 'Članak B')
    html = client.get('/tech-magazin/a').get_data(as_text=True)
    assert 'Članak A' in html
    assert 'Još iz Tech Magazina' in html and 'Članak B' in html
    assert 'Otvori konfigurator' in html


def test_static_pages_render(client):
    for url, text in (('/o-nama', 'Kontakt'), ('/politika-privatnosti', 'Kolačići'), ('/uslovi-koriscenja', 'Porudžbine i plaćanje')):
        res = client.get(url)
        assert res.status_code == 200, url
        assert text in res.get_data(as_text=True), url
